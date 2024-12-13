# Import required Django modules
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json

# Import models from current app and base app
from .models import *
from base.models import *

# Import Google's Generative AI library and datetime
import google.generativeai as genai
from datetime import datetime

# Configure Gemini API with key
genai.configure(api_key="AIzaSyDIMVFYAcZOWDGe6RjRUmSnNjxEO5cH1fE")

# View to render the chatbot interface
@login_required
def Chatbot(request):
    user = request.user
    current_date = datetime.now()
    
    # Get last 50 messages for this user
    messages = Message.objects.filter(user=user).order_by('time')[:50]
    
    context = {
        'user': user, 
        'messages': messages,
        'current_date': current_date
    }
    
    return render(request, 'chatbot/chatbot.html', context)

# View to handle chat messages and object creation
@login_required
def handle_message(request):
    user = request.user
    
    # Only allow POST requests
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parse the request data
        data = json.loads(request.body)
        user_message = data.get('message')
        
        # Get chat history for context
        previous_messages = Message.objects.filter(user=user).order_by('time')
        history = []
        for msg in previous_messages:
            history.append({"role": "user", "parts": [msg.message]})
            history.append({"role": "model", "parts": [msg.response]})

        # Initialize Gemini chat model with history
        model = genai.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=history)
        
        # Get initial response from model
        response = chat.send_message([user_message])
        bot_response = response.text

        # Define required properties for each object type
        object_properties = {
            "class": ["name"],
            "assignment": ["class", "name", "description", "due_date", "status"],
            "exam": ["class", "name", "date", "duration"]
        }
        
        # Get or create task for tracking object creation
        latest_task = Task.objects.filter(user=user).order_by('-start_date').first()
            
        if latest_task and not latest_task.is_done:
            task = latest_task
        else:
            task = Task.objects.create(
                user=user,
                object=None,
                properties={},
                is_done=False
            )
     
        # Handle case where object type isn't set
        if task.object is None:
            # Check message for object type keywords
            user_message_lower = user_message.lower()
            object_type = None
            
            if "exam" in user_message_lower or "test" in user_message_lower:
                object_type = "exam"
            elif "class" in user_message_lower or "course" in user_message_lower or "subject" in user_message_lower:
                object_type = "class" 
            elif "assignment" in user_message_lower or "task" in user_message_lower or "homework" in user_message_lower:
                object_type = "assignment"
            
            # If object type found, save and ask for first property
            if object_type:
                task.object = object_type
                task.save()
                
                required_props = object_properties[task.object]
                next_prop = required_props[0]
                prompt = f"What is the {next_prop} for this {task.object}?"
                
                Message.objects.create(
                    user=user,
                    message=user_message,
                    response=prompt,
                )
                return JsonResponse({'response': prompt})
            
            # If no object type found, ask model to determine it
            prompt = "What object do you want to create?"
            object_response = chat.send_message([prompt])
            object_bot_response = object_response.text
            
            # Parse model response for object type
            response_lower = object_bot_response.lower().strip()
            if "exam" in response_lower or "test" in response_lower:
                object_type = "exam"
            elif "class" in response_lower or "course" in response_lower or "subject" in response_lower:
                object_type = "class"
            elif "assignment" in response_lower or "task" in response_lower or "homework" in response_lower:
                object_type = "assignment"
            else:
                object_type = "none"
                
            # Save message and update task
            Message.objects.create(
                user=user,
                message=user_message,
                response=prompt,
            )
            if object_type != "none":
                task.object = object_type
                task.save()
            else:
                task.delete()
            return JsonResponse({'response': prompt})
        
        # Handle collecting required properties for the object
        elif task.properties is None or len(task.properties) < len(object_properties[task.object]):
            required_props = object_properties[task.object]
            current_props = task.properties if task.properties else {}
            
            # Get next required property
            next_prop = required_props[len(current_props)]
            
            # Validate property value with model
            validation_prompt = f"Is this a valid {next_prop} for a {task.object}? Answer only 'yes' or 'no': {user_message}"
            validation_response = chat.send_message([validation_prompt])
            is_valid = validation_response.text.strip().lower() == 'yes'
            
            if is_valid:
                # Save valid property and determine next step
                current_props[next_prop] = user_message
                task.properties = current_props
                task.save()
                
                if len(current_props) < len(required_props):
                    next_prop = required_props[len(current_props)]
                    prompt = f"What is the {next_prop} for this {task.object}?"
                else:
                    prompt = f"Great! I've collected all the required information."
            else:
                prompt = f"That doesn't seem to be a valid {next_prop}. Please provide a valid {next_prop} for this {task.object}."
            
            # Debug prints
            print(task.properties)
            print(len(task.properties))
            print(len(object_properties[task.object]))
            
            # If all properties collected, create the object
            if task.object and task.properties and len(task.properties) == len(object_properties[task.object]):
                task.is_done = True
                task.save()

                create_object(task)
 
                prompt = f"Great! I've created your {task.object} object with all the required information! Go have a look..."

            Message.objects.create(
                user=user,
                message=user_message,
                response=prompt,
            )
            return JsonResponse({'response': prompt})
        
        # Save regular chat message and response
        Message.objects.create(
            user=user,
            message=user_message,
            response=bot_response,
        )
        
        return JsonResponse({'response': bot_response})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

# Helper function to create objects based on collected properties
def create_object(task):
    # Initialize Gemini model to help with validation
    model = genai.GenerativeModel("gemini-1.5-flash")

    if task.object == "assignment":        
        # Convert user-provided due date to proper datetime format
        validation_prompt = f"turn this date into the format of YYYY-MM-DD HH:MM: {task.properties['due_date']}"
        due_date_text = model.generate_content(validation_prompt)
        due_date = datetime.strptime(due_date_text.text.strip(), "%Y-%d-%m %H:%M")
        
        # Get the associated class object
        class_obj = Class.objects.get(user=task.user, name=task.properties["class"])
        
        # Create new Assignment with validated data
        Assignment.objects.create(
            class_obj=class_obj,
            name=task.properties["name"], 
            description=task.properties["description"],
            due_date=due_date,
            status=task.properties["status"]
        )
    elif task.object == "exam":        
        # Convert user-provided date to proper date format
        validation_prompt = f"turn this date into the format of YYYY-MM-DD: {task.properties['date']}"
        date_text = model.generate_content(validation_prompt)
        date = datetime.strptime(date_text.text.strip(), "%Y-%d-%m")
        
        # Get the associated class object
        class_obj = Class.objects.get(user=task.user, name=task.properties["class"])
        
        # Extract duration in minutes from user input
        duration_prompt = f"Extract only the number of minutes as an integer from this text: {task.properties['duration']}"
        duration_text = model.generate_content(duration_prompt)
        duration = int(duration_text.text.strip())
        
        # Create new Exam with validated data
        Exam.objects.create(
            class_obj=class_obj,
            name=task.properties["name"],
            date=date,
            duration=duration
        )
    elif task.object == "class":
        # Create new Class object (no validation needed)
        Class.objects.create(
            user=task.user,
            name=task.properties["name"]
        )
