import streamlit as st
import pandas as pd
import datetime
import time
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import random

# Set page configuration
st.set_page_config(
    page_title="AI Day Agent Planner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve appearance
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    .task-complete {
        text-decoration: line-through;
        color: gray;
    }
    .highlight {
        background-color: #f0f8ff;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
    }
    h1, h2, h3 {
        color: #2C3E50;
    }
    .stSidebar .sidebar-content {
        background-color: #f5f5f5;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'current_task' not in st.session_state:
    st.session_state.current_task = None
if 'progress_history' not in st.session_state:
    st.session_state.progress_history = []
if 'schedule_adjusted' not in st.session_state:
    st.session_state.schedule_adjusted = False
if 'task_suggestions' not in st.session_state:
    st.session_state.task_suggestions = [
        "Morning workout",
        "Check and respond to emails",
        "Team meeting",
        "Project work",
        "Lunch break",
        "Client call",
        "Review daily progress",
        "Plan for tomorrow"
    ]

# App header
st.title("📅 AI Day Agent Planner")
st.markdown("Let our AI agent organize your daily activities, track your pace, and adapt your schedule in real time for a stress-free experience.")

# Sidebar for task input and management
with st.sidebar:
    st.header("Task Management")
    st.subheader("Add New Task")
    
    # Task input form
    with st.form(key="task_form"):
        task_name = st.text_input("Task Name")
        
        col1, col2 = st.columns(2)
        with col1:
            task_duration = st.number_input("Duration (minutes)", min_value=5, max_value=480, value=30, step=5)
        with col2:
            task_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
        
        task_category = st.selectbox("Category", ["Work", "Personal", "Health", "Learning", "Other"])
        task_notes = st.text_area("Notes (Optional)")
        
        submit_button = st.form_submit_button(label="Add Task")
        
        if submit_button and task_name:
            new_task = {
                "name": task_name,
                "duration": task_duration,
                "priority": task_priority,
                "category": task_category,
                "notes": task_notes,
                "completed": False,
                "actual_duration": 0,
                "start_time": None,
                "end_time": None
            }
            st.session_state.tasks.append(new_task)
            st.success(f"Task '{task_name}' added successfully!")

    # Quick add from suggestions
    st.subheader("Quick Add")
    if st.session_state.task_suggestions:
        selected_suggestion = st.selectbox("Add from suggestions:", 
                                          ["Select a suggestion..."] + st.session_state.task_suggestions)
        if selected_suggestion != "Select a suggestion...":
            if st.button("Quick Add"):
                new_task = {
                    "name": selected_suggestion,
                    "duration": 30,  # Default duration
                    "priority": "Medium",  # Default priority
                    "category": "Work" if "meeting" in selected_suggestion.lower() or "email" in selected_suggestion.lower() or "work" in selected_suggestion.lower() else "Personal",
                    "notes": "",
                    "completed": False,
                    "actual_duration": 0,
                    "start_time": None,
                    "end_time": None
                }
                st.session_state.tasks.append(new_task)
                st.success(f"Quick task '{selected_suggestion}' added!")

    # Reset button
    if st.button("Reset All Data"):
        st.session_state.tasks = []
        st.session_state.completed_tasks = []
        st.session_state.start_time = None
        st.session_state.notifications = []
        st.session_state.current_task = None
        st.session_state.progress_history = []
        st.session_state.schedule_adjusted = False
        st.success("All data has been reset!")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Daily Schedule")
    
    # Start day button
    if st.session_state.start_time is None:
        if st.button("Start Your Day", key="start_day"):
            st.session_state.start_time = datetime.now()
            
            # Sort tasks by priority
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            st.session_state.tasks.sort(key=lambda x: priority_order.get(x["priority"], 999))
            
            if st.session_state.tasks:
                st.session_state.current_task = 0
                st.session_state.tasks[0]["start_time"] = datetime.now()
                
                # Add initial progress data point
                st.session_state.progress_history.append({
                    "timestamp": datetime.now(),
                    "completed_tasks": 0,
                    "total_tasks": len(st.session_state.tasks),
                    "completion_percentage": 0
                })
    
    # Display current schedule
    if st.session_state.tasks:
        current_time = datetime.now()
        total_minutes = 0
        
        for i, task in enumerate(st.session_state.tasks):
            # Calculate expected start time
            if st.session_state.start_time is not None:
                expected_start = st.session_state.start_time + timedelta(minutes=total_minutes)
                expected_end = expected_start + timedelta(minutes=task["duration"])
                
                # Format the time information
                start_time_str = expected_start.strftime("%I:%M %p")
                end_time_str = expected_end.strftime("%I:%M %p")
                time_info = f"{start_time_str} - {end_time_str}"
            else:
                time_info = f"Duration: {task['duration']} min"
            
            # Create a container for each task
            task_container = st.container()
            
            with task_container:
                cols = st.columns([0.7, 0.15, 0.15])
                
                # Style based on task status
                task_class = "task-complete" if task.get("completed", False) else ""
                current_indicator = "→ " if i == st.session_state.current_task and st.session_state.start_time is not None else ""
                
                with cols[0]:
                    task_text = f"{current_indicator}{task['name']} ({task['priority']} priority)"
                    if task_class:
                        st.markdown(f"<span class='{task_class}'>{task_text}</span>", unsafe_allow_html=True)
                    else:
                        st.write(task_text)
                    
                    # Add category badge and notes if present
                    if task.get("notes"):
                        st.caption(f"Category: {task['category']} | Notes: {task['notes']}")
                    else:
                        st.caption(f"Category: {task['category']}")
                
                with cols[1]:
                    st.write(time_info)
                
                with cols[2]:
                    # Mark as complete button (only for current task when day is started)
                    if i == st.session_state.current_task and st.session_state.start_time is not None and not task.get("completed", False):
                        if st.button("Complete", key=f"complete_{i}"):
                            task["completed"] = True
                            task["end_time"] = datetime.now()
                            
                            # Calculate actual duration
                            if task["start_time"]:
                                task["actual_duration"] = (task["end_time"] - task["start_time"]).total_seconds() / 60
                            
                            # Move to completed tasks
                            st.session_state.completed_tasks.append(task.copy())
                            
                            # Update progress history
                            completed_count = sum(1 for t in st.session_state.tasks if t.get("completed", False))
                            st.session_state.progress_history.append({
                                "timestamp": datetime.now(),
                                "completed_tasks": completed_count,
                                "total_tasks": len(st.session_state.tasks),
                                "completion_percentage": (completed_count / len(st.session_state.tasks)) * 100
                            })
                            
                            # Move to next task if available
                            if i + 1 < len(st.session_state.tasks):
                                st.session_state.current_task = i + 1
                                st.session_state.tasks[i + 1]["start_time"] = datetime.now()
                            else:
                                st.session_state.current_task = None
                            
                            # Force refresh
                            st.experimental_rerun()
            
            # Add to total duration for next task calculation
            total_minutes += task["duration"]
        
        # Show overall progress
        completed_count = sum(1 for task in st.session_state.tasks if task.get("completed", False))
        if st.session_state.tasks:
            progress_percentage = completed_count / len(st.session_state.tasks)
            st.progress(progress_percentage)
            st.write(f"Progress: {completed_count}/{len(st.session_state.tasks)} tasks completed ({int(progress_percentage * 100)}%)")
    else:
        st.info("No tasks added yet. Use the sidebar to add tasks to your schedule.")

    # AI recommendations section
    st.header("AI Recommendations")
    
    if st.session_state.start_time is not None and st.session_state.tasks:
        # Check if schedule needs adjustment
        current_task_idx = st.session_state.current_task
        
        if current_task_idx is not None and current_task_idx < len(st.session_state.tasks):
            current_task = st.session_state.tasks[current_task_idx]
            
            # Calculate if we're behind schedule
            if current_task.get("start_time") and not st.session_state.schedule_adjusted:
                expected_start_time = None
                total_minutes = 0
                
                # Calculate expected start time for current task
                for i in range(current_task_idx):
                    total_minutes += st.session_state.tasks[i].get("duration", 0)
                
                expected_start_time = st.session_state.start_time + timedelta(minutes=total_minutes)
                actual_start_time = current_task.get("start_time")
                
                # If we're more than 15 minutes behind schedule, suggest adjustment
                if actual_start_time and actual_start_time > expected_start_time + timedelta(minutes=15):
                    st.warning("You're behind schedule! Would you like the AI to adjust your remaining tasks?")
                    
                    if st.button("Adjust Schedule"):
                        # Simple algorithm to reduce remaining tasks by 10-20%
                        for i in range(current_task_idx, len(st.session_state.tasks)):
                            task = st.session_state.tasks[i]
                            if task["duration"] > 15:  # Don't reduce tasks that are already short
                                reduction = random.uniform(0.1, 0.2)  # Reduce by 10-20%
                                task["duration"] = int(task["duration"] * (1 - reduction))
                        
                        st.session_state.schedule_adjusted = True
                        st.success("Schedule adjusted! Task durations have been optimized for the remaining day.")
                        
                        # Force refresh to show updated schedule
                        st.experimental_rerun()
            
            # Provide contextual recommendations
            recommendations = []
            
            # If current task is high priority and taking longer than expected
            if current_task.get("priority") == "High" and current_task.get("start_time"):
                time_spent = (datetime.now() - current_task["start_time"]).total_seconds() / 60
                if time_spent > current_task["duration"] * 0.8:
                    recommendations.append("Your current high-priority task is taking longer than expected. Consider focusing solely on this task and postponing lower priority items if needed.")
            
            # If we have completed more than 50% of tasks
            completed_count = sum(1 for task in st.session_state.tasks if task.get("completed", False))
            if st.session_state.tasks and completed_count / len(st.session_state.tasks) > 0.5:
                recommendations.append("Great progress today! You've completed over half of your planned tasks. Consider taking a short break to maintain productivity for the remaining tasks.")
            
            # If there are too many high priority tasks remaining
            high_priority_remaining = sum(1 for task in st.session_state.tasks[current_task_idx:] if task.get("priority") == "High" and not task.get("completed", False))
            if high_priority_remaining > 3:
                recommendations.append("You have several high-priority tasks remaining. Consider re-evaluating their priorities or delegating some if possible.")
            
            # Display recommendations
            if recommendations:
                for rec in recommendations:
                    st.markdown(f"<div class='highlight'>💡 {rec}</div>", unsafe_allow_html=True)
            else:
                st.info("You're on track with your schedule. Keep up the good work!")
        
        # Check if all tasks are completed
        if all(task.get("completed", False) for task in st.session_state.tasks) and st.session_state.tasks:
            st.balloons()
            st.success("🎉 Congratulations! You have completed all tasks for today!")
    else:
        st.info("Start your day and add tasks to get AI recommendations.")

with col2:
    st.header("Analytics & Insights")
    
    # Task distribution by category
    if st.session_state.tasks:
        st.subheader("Tasks by Category")
        categories = {}
        for task in st.session_state.tasks:
            categories[task["category"]] = categories.get(task["category"], 0) + 1
        
        # Create dataframe for pie chart
        df_categories = pd.DataFrame({
            "Category": list(categories.keys()),
            "Count": list(categories.values())
        })
        
        fig = px.pie(df_categories, values="Count", names="Category", title="Task Distribution by Category")
        st.plotly_chart(fig, use_container_width=True)
    
    # Progress over time chart
    if st.session_state.progress_history:
        st.subheader("Progress Over Time")
        
        # Create a dataframe from progress history
        df_progress = pd.DataFrame(st.session_state.progress_history)
        
        # Create the line chart
        fig = px.line(
            df_progress, 
            x="timestamp", 
            y="completion_percentage",
            title="Task Completion Progress"
        )
        fig.update_layout(yaxis_title="Completion (%)", xaxis_title="Time")
        st.plotly_chart(fig, use_container_width=True)
    
    # Notifications & Reminders
    st.subheader("Notifications")
    
    # Add sample notifications if none exist
    if not st.session_state.notifications and st.session_state.start_time is not None:
        st.session_state.notifications = [
            {"message": "Welcome to your AI Day Planner! I'll help you stay on track.", "time": datetime.now().strftime("%I:%M %p")},
            {"message": "Remember to take short breaks between tasks for optimal productivity.", "time": datetime.now().strftime("%I:%M %p")}
        ]
    
    # Display notifications
    notification_container = st.container()
    with notification_container:
        if st.session_state.notifications:
            for notification in st.session_state.notifications:
                st.markdown(f"**{notification['time']}**: {notification['message']}")
        else:
            st.info("No notifications yet.")
    
    # Productivity tips
    st.subheader("Productivity Tips")
    tips = [
        "Try the Pomodoro Technique: 25 minutes of focused work followed by a 5-minute break.",
        "Tackle your most challenging task first thing in the morning when your energy is highest.",
        "Block distracting websites during focused work periods.",
        "Stay hydrated throughout the day to maintain optimal brain function.",
        "Take a short walk between tasks to refresh your mind."
    ]
    
    # Show a random tip
    st.info(random.choice(tips))

# Function to simulate real-time updates (in a real app, this would be better implemented with proper async mechanisms)
if st.session_state.start_time is not None:
    # Simulate time passing (in a real app, you'd use a proper timer)
    current_time = datetime.now()
    
    # Add a new notification every few minutes (simulated)
    notification_time = current_time - st.session_state.start_time
    if len(st.session_state.notifications) < 5 and notification_time.total_seconds() % 60 < 1 and random.random() < 0.05:
        new_notifications = [
            "Taking a 5-minute break now could boost your productivity for the next task.",
            "You're making good progress! Keep going!",
            "Remember to stay hydrated for optimal focus.",
            "Consider adjusting your posture to prevent strain during computer work.",
            "It might be a good time to check in with your team on project progress."
        ]
        
        st.session_state.notifications.append({
            "message": random.choice(new_notifications),
            "time": current_time.strftime("%I:%M %p")
        })

# Footer
st.markdown("---")
st.markdown("© 2025 AI Day Agent Planner - Helping you stay organized and stress-free")