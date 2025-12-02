# app.py
from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime
from fpdf import FPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key for Groq
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("ERROR: GROQ_API_KEY environment variable is not set!")
    print("Please add GROQ_API_KEY to your .env file")
    exit(1)

# Set environment variable for litellm
os.environ["GROQ_API_KEY"] = api_key

# Import litellm and CrewAI
import litellm
from crewai import Agent, Task, Crew

litellm.set_verbose = False

# Store plans in memory
study_plans = {}

# LLM configuration - Groq (using Llama model)
llm = "groq/llama-3.3-70b-versatile"
print(f"✓ Using LLM: {llm}")

# ========================================================================
# CREATE AGENTS
# ========================================================================

print("Creating agents...")

syllabus_analyzer = Agent(
    role="Syllabus Analyzer",
    goal="Break down syllabus text into structured topics with time estimates",
    backstory="Expert at analyzing educational content and creating structured learning paths",
    llm=llm,
    verbose=False
)

schedule_architect = Agent(
    role="Schedule Architect", 
    goal="Create practical day-by-day study schedules",
    backstory="Specialist in time management and creating realistic study plans",
    llm=llm,
    verbose=False
)

resource_recommender = Agent(
    role="Resource Recommender",
    goal="Suggest relevant study materials and resources",
    backstory="Expert at matching learning resources to topics and learning styles",
    llm=llm,
    verbose=False
)

print("✓ Agents created successfully")

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def analyze_learning_preferences_local(prefs_text):
    """Simple local learning style analysis"""
    prefs_lower = prefs_text.lower()
    
    primary = "reading-writing"
    if "visual" in prefs_lower:
        primary = "visual"
    elif "audio" in prefs_lower or "auditory" in prefs_lower:
        primary = "auditory"
    elif "kinesthetic" in prefs_lower or "hands" in prefs_lower:
        primary = "kinesthetic"
    
    methods = {
        "visual": ["video lectures", "diagrams", "mind maps", "flashcards"],
        "auditory": ["podcasts", "audio books", "group discussions", "lectures"],
        "kinesthetic": ["hands-on practice", "labs", "projects", "simulations"],
        "reading-writing": ["textbooks", "note-taking", "written summaries", "articles"]
    }
    
    return {
        "primary_learning_style": primary,
        "recommended_study_methods": methods.get(primary, methods["reading-writing"]),
        "personalized_tips": "Use 45-90 minute focused sessions with breaks. Apply active recall and spaced repetition."
    }

def generate_progress_tracking_local(duration_days):
    """Generate simple progress tracking"""
    checkpoints = []
    interval = max(7, duration_days // 4)
    
    for i in range(1, 5):
        day = min(duration_days, i * interval)
        checkpoints.append({
            "day": day,
            "checkpoint": f"Review Week {i}",
            "assessment": "Quiz + practical exercise"
        })
    
    return {
        "checkpoint_schedule": checkpoints,
        "tracking_metrics": [
            "Daily session completion",
            "Topic understanding scores",
            "Practice problem accuracy"
        ]
    }

def extract_json_from_response(text):
    """Extract JSON from agent response that may have code fences"""
    text = text.strip()
    
    # Remove code fences if present
    if text.startswith('```'):
        lines = text.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('```'):
                if start_idx is None:
                    start_idx = i + 1
                else:
                    end_idx = i
                    break
        
        if start_idx and end_idx:
            text = '\n'.join(lines[start_idx:end_idx]).strip()
    
    # Try to parse JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Text: {text[:200]}...")
        # Return minimal valid structure
        return {"error": "Failed to parse JSON response"}

# ========================================================================
# STUDY PLAN GENERATION
# ========================================================================

def create_study_plan(syllabus_text, learning_preferences, study_duration_days):
    """Generate comprehensive study plan"""
    
    print("\n" + "="*80)
    print("GENERATING STUDY PLAN")
    print("="*80)
    
    try:
        # 1. Local learning analysis
        print("\n[1/4] Analyzing learning preferences...")
        learning_analysis = analyze_learning_preferences_local(learning_preferences)
        print("✓ Learning analysis complete")
        
        # 2. Syllabus analysis
        print("\n[2/4] Analyzing syllabus...")
        syllabus_task = Task(
            description=f"""Analyze this syllabus and return ONLY valid JSON with no extra text:

SYLLABUS:
{syllabus_text[:2000]}

Return JSON with this exact structure:
{{
  "subjects": [
    {{
      "name": "Subject Name",
      "chapters": [
        {{"name": "Chapter", "estimated_hours": 5, "difficulty": "medium"}}
      ]
    }}
  ],
  "total_estimated_hours": 100
}}""",
            expected_output="JSON syllabus analysis",
            agent=syllabus_analyzer
        )
        
        syllabus_crew = Crew(agents=[syllabus_analyzer], tasks=[syllabus_task], verbose=False)
        syllabus_result = syllabus_crew.kickoff()
        syllabus_analysis = extract_json_from_response(str(syllabus_result))
        print("✓ Syllabus analysis complete")
        
        # 3. Schedule creation
        print("\n[3/4] Creating study schedule...")
        schedule_task = Task(
            description=f"""Create a {study_duration_days}-day study schedule. Return ONLY valid JSON with no extra text:

Subjects: {json.dumps(syllabus_analysis.get('subjects', [])[:2])}
Learning Style: {learning_analysis['primary_learning_style']}

Return JSON with this structure:
{{
  "schedule": [
    {{
      "day": 1,
      "date": "2025-12-03",
      "sessions": [
        {{"time": "09:00-11:00", "topic": "Topic", "activities": ["Read", "Practice"]}}
      ]
    }}
  ]
}}""",
            expected_output="JSON schedule",
            agent=schedule_architect
        )
        
        schedule_crew = Crew(agents=[schedule_architect], tasks=[schedule_task], verbose=False)
        schedule_result = schedule_crew.kickoff()
        schedule = extract_json_from_response(str(schedule_result))
        print("✓ Schedule created")
        
        # 4. Resource recommendations
        print("\n[4/4] Recommending resources...")
        topics = [s['name'] for s in syllabus_analysis.get('subjects', [])[:3]]
        resource_task = Task(
            description=f"""Recommend study resources for: {', '.join(topics)}
Learning style: {learning_analysis['primary_learning_style']}

Return ONLY valid JSON with no extra text:
{{
  "resource_recommendations": [
    {{
      "topic": "Topic",
      "resources": [
        {{"type": "video", "name": "Resource Name", "description": "Why useful"}}
      ]
    }}
  ]
}}""",
            expected_output="JSON resources",
            agent=resource_recommender
        )
        
        resource_crew = Crew(agents=[resource_recommender], tasks=[resource_task], verbose=False)
        resource_result = resource_crew.kickoff()
        resources = extract_json_from_response(str(resource_result))
        print("✓ Resources recommended")
        
        # 5. Progress tracking (local)
        progress_system = generate_progress_tracking_local(study_duration_days)
        
        print("\n" + "="*80)
        print("✓ STUDY PLAN COMPLETE")
        print("="*80 + "\n")
        
        return {
            "created_at": datetime.now().isoformat(),
            "duration_days": study_duration_days,
            "syllabus_analysis": syllabus_analysis,
            "learning_analysis": learning_analysis,
            "schedule": schedule,
            "resources": resources,
            "progress_tracking": progress_system
        }
        
    except Exception as e:
        print(f"✗ Error in study plan generation: {e}")
        import traceback
        traceback.print_exc()
        raise

# ========================================================================
# PDF GENERATION
# ========================================================================

def generate_study_plan_pdf(study_plan):
    """Generate PDF report"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Personalized Study Plan", ln=True, align='C')
    pdf.ln(5)
    
    # Metadata
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Created: {study_plan['created_at'][:10]}", ln=True)
    pdf.cell(0, 5, f"Duration: {study_plan['duration_days']} days", ln=True)
    pdf.ln(5)
    
    # Syllabus
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Syllabus Overview", ln=True)
    pdf.set_font("Arial", size=10)
    
    syllabus = study_plan.get('syllabus_analysis', {})
    if 'error' not in syllabus:
        pdf.cell(0, 6, f"Total Hours: {syllabus.get('total_estimated_hours', 'N/A')}", ln=True)
        
        for subject in syllabus.get('subjects', [])[:3]:
            pdf.cell(0, 6, f"- {subject.get('name', 'Unknown')}", ln=True)
    pdf.ln(5)
    
    # Learning Style
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Learning Approach", ln=True)
    pdf.set_font("Arial", size=10)
    
    learning = study_plan.get('learning_analysis', {})
    pdf.cell(0, 6, f"Style: {learning.get('primary_learning_style', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Schedule Sample
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Schedule (First 3 Days)", ln=True)
    pdf.set_font("Arial", size=9)
    
    schedule = study_plan.get('schedule', {})
    if 'error' not in schedule:
        for day in schedule.get('schedule', [])[:3]:
            pdf.cell(0, 5, f"Day {day.get('day')}: {day.get('date', 'N/A')}", ln=True)
            for session in day.get('sessions', [])[:2]:
                pdf.cell(0, 4, f"  - {session.get('time')}: {session.get('topic')}", ln=True)
    
    return pdf.output(dest='S').encode('latin1')

# ========================================================================
# FLASK ROUTES
# ========================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    """Generate study plan endpoint"""
    print("\n[API] Generate plan request received")
    
    try:
        # Get data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        syllabus_text = data.get('syllabus_text', '').strip()
        learning_prefs = data.get('learning_preferences', '').strip()
        duration = int(data.get('study_duration_days', 30))
        
        # Validate
        if not syllabus_text:
            return jsonify({'error': 'Syllabus text is required'}), 400
        
        if not learning_prefs:
            return jsonify({'error': 'Learning preferences are required'}), 400
        
        print(f"[API] Syllabus length: {len(syllabus_text)} chars")
        print(f"[API] Duration: {duration} days")
        
        # Generate plan
        study_plan = create_study_plan(syllabus_text, learning_prefs, duration)
        
        # Store plan
        plan_id = f"plan_{int(datetime.now().timestamp())}"
        study_plans[plan_id] = study_plan
        
        print(f"[API] ✓ Plan generated: {plan_id}")
        
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'message': 'Study plan generated successfully',
            'summary': {
                'created_at': study_plan['created_at'],
                'duration_days': study_plan['duration_days'],
                'total_estimated_hours': study_plan['syllabus_analysis'].get('total_estimated_hours', 'N/A'),
                'primary_learning_style': study_plan['learning_analysis']['primary_learning_style']
            }
        }), 200
        
    except Exception as e:
        print(f"[API] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/plan/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get plan details"""
    if plan_id not in study_plans:
        return jsonify({'error': 'Plan not found'}), 404
    
    return jsonify({
        'success': True,
        'plan': study_plans[plan_id]
    }), 200

@app.route('/api/plan/<plan_id>/pdf', methods=['GET'])
def download_pdf(plan_id):
    """Download plan as PDF"""
    if plan_id not in study_plans:
        return jsonify({'error': 'Plan not found'}), 404
    
    try:
        pdf_bytes = generate_study_plan_pdf(study_plans[plan_id])
        return pdf_bytes, 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': f'attachment; filename=study_plan_{plan_id}.pdf'
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'Study Plan Generator',
        'agents': 3,
        'llm': llm,
        'timestamp': datetime.now().isoformat()
    }), 200

# ========================================================================
# RUN APP
# ========================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("STUDY PLAN GENERATOR - AI-POWERED WITH GROQ")
    print("="*80)
    print("\n✓ 3 CrewAI Agents Active:")
    print("  1. Syllabus Analyzer")
    print("  2. Schedule Architect")
    print("  3. Resource Recommender")
    print(f"\n✓ LLM: {llm}")
    print("✓ Ready to generate personalized study plans!")
    print("="*80 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)