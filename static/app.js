// Global variables
let currentPlanId = null;
let currentPlanResult = null;

// Ensure page starts at top
window.addEventListener("load", () => {
    window.scrollTo(0, 0);
});

// ============================================================================
// SCREEN NAVIGATION
// ============================================================================

function showPlanForm() {
    document.getElementById("home-screen").classList.remove("active");
    document.getElementById("plan-form-screen").classList.add("active");
    window.scrollTo(0, 0);
}

function backToHome() {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    document.getElementById("home-screen").classList.add("active");
    
    // Reset form
    document.getElementById('study-plan-form').reset();
    document.getElementById('form-loader').style.display = 'none';
    document.getElementById('form-status').textContent = '';
    
    // Clear plan data
    currentPlanId = null;
    currentPlanResult = null;
    
    window.scrollTo(0, 0);
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================

function showToast(message, type = 'info', duration = 3000) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// ============================================================================
// FORM SUBMISSION
// ============================================================================

document.getElementById('study-plan-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    console.log('[Form] Submit triggered');

    // Get form values
    const syllabusText = document.getElementById('syllabus-text').value.trim();
    const learningStyle = document.getElementById('learning-style').value;
    const studyHours = document.getElementById('study-hours').value;
    const learningPace = document.getElementById('learn-pace').value;
    const additionalPrefs = document.getElementById('additional-prefs').value.trim();
    const studyDuration = document.getElementById('study-duration').value;

    // Validate
    if (!syllabusText) {
        showToast('⚠️ Please enter your syllabus text', 'error');
        return;
    }

    if (!learningStyle || !studyHours || !learningPace) {
        showToast('⚠️ Please fill in all required fields', 'error');
        return;
    }

    // Combine learning preferences
    const learningPreferences = `Learning Style: ${learningStyle}. ` +
        `Study Hours Per Day: ${studyHours}. ` +
        `Learning Pace: ${learningPace}. ` +
        `Additional Preferences: ${additionalPrefs || 'None'}`;

    const payload = {
        syllabus_text: syllabusText,
        learning_preferences: learningPreferences,
        study_duration_days: parseInt(studyDuration)
    };

    console.log('[Form] Payload:', {
        syllabusLength: syllabusText.length,
        duration: studyDuration,
        style: learningStyle
    });

    // Show loader
    document.getElementById('form-loader').style.display = 'block';
    document.getElementById('form-status').textContent = '';

    try {
        console.log('[API] Sending request...');
        
        const response = await fetch('/api/generate-plan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        console.log('[API] Response status:', response.status);

        const result = await response.json();
        console.log('[API] Result:', result);

        if (!response.ok) {
            throw new Error(result.error || 'Failed to generate study plan');
        }

        // Store plan ID and result
        currentPlanId = result.plan_id;
        currentPlanResult = result;

        // Hide loader
        document.getElementById('form-loader').style.display = 'none';

        // Show results
        displayPlanResults(result);

        showToast('✅ Study plan generated successfully!', 'success', 4000);

    } catch (error) {
        console.error('[API] Error:', error);
        
        document.getElementById('form-loader').style.display = 'none';
        document.getElementById('form-status').textContent = `Error: ${error.message}`;
        
        showToast(`❌ Error: ${error.message}`, 'error', 5000);
    }
});

// ============================================================================
// RESULTS DISPLAY
// ============================================================================

function displayPlanResults(result) {
    console.log('[Results] Displaying plan results');
    
    // Switch screens
    document.getElementById('plan-form-screen').classList.remove('active');
    document.getElementById('results-screen').classList.add('active');
    
    // Update summary
    document.getElementById('summary-plan-id').textContent = result.plan_id.substring(5, 15);
    document.getElementById('summary-duration').textContent = `${result.summary.duration_days} days`;
    document.getElementById('summary-hours').textContent = result.summary.total_estimated_hours || 'Varies';
    document.getElementById('summary-style').textContent = result.summary.primary_learning_style || 'Mixed';

    // Hide details initially
    document.getElementById('plan-details').style.display = 'none';

    window.scrollTo(0, 0);
}

function downloadPlan() {
    if (!currentPlanId) {
        showToast('⚠️ No plan available for download', 'error');
        return;
    }

    console.log('[Download] Initiating PDF download for:', currentPlanId);

    showToast('📥 Preparing your study plan PDF...', 'info');

    // Create download link
    const downloadUrl = `/api/plan/${currentPlanId}/pdf`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `study_plan_${currentPlanId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => {
        showToast('✅ PDF download started!', 'success');
    }, 1000);
}

function viewPlanDetails() {
    const detailsDiv = document.getElementById('plan-details');
    
    if (detailsDiv.style.display === 'none') {
        detailsDiv.style.display = 'block';
        loadPlanDetails();
    } else {
        detailsDiv.style.display = 'none';
    }
}

async function loadPlanDetails() {
    if (!currentPlanId) {
        showToast('⚠️ No plan data available', 'error');
        return;
    }

    console.log('[Details] Loading plan details for:', currentPlanId);

    try {
        const response = await fetch(`/api/plan/${currentPlanId}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to load plan details');
        }

        const plan = result.plan;
        let html = '';

        // Syllabus Analysis Section
        if (plan.syllabus_analysis && !plan.syllabus_analysis.error) {
            html += `
                <div class="detail-section">
                    <h4>📚 Syllabus Analysis</h4>
                    <p><strong>Total Estimated Hours:</strong> ${plan.syllabus_analysis.total_estimated_hours || 'N/A'}</p>
            `;
            
            if (plan.syllabus_analysis.subjects && plan.syllabus_analysis.subjects.length > 0) {
                html += '<p><strong>Subjects/Modules:</strong></p><ul>';
                plan.syllabus_analysis.subjects.forEach(subject => {
                    html += `<li><strong>${subject.name}</strong> (${subject.chapters?.length || 0} chapters)</li>`;
                    
                    // Show first 3 chapters
                    if (subject.chapters && subject.chapters.length > 0) {
                        html += '<ul>';
                        subject.chapters.slice(0, 3).forEach(chapter => {
                            html += `<li>${chapter.name} - ${chapter.estimated_hours || 0}h (${chapter.difficulty || 'medium'})</li>`;
                        });
                        if (subject.chapters.length > 3) {
                            html += `<li><em>...and ${subject.chapters.length - 3} more chapters</em></li>`;
                        }
                        html += '</ul>';
                    }
                });
                html += '</ul>';
            }
            
            html += '</div>';
        }

        // Learning Analysis Section
        if (plan.learning_analysis && !plan.learning_analysis.error) {
            html += `
                <div class="detail-section">
                    <h4>🎨 Your Learning Profile</h4>
                    <p><strong>Primary Learning Style:</strong> ${plan.learning_analysis.primary_learning_style || 'N/A'}</p>
            `;
            
            if (plan.learning_analysis.recommended_study_methods && plan.learning_analysis.recommended_study_methods.length > 0) {
                html += '<p><strong>Recommended Study Methods:</strong></p><ul>';
                plan.learning_analysis.recommended_study_methods.forEach(method => {
                    html += `<li>${method}</li>`;
                });
                html += '</ul>';
            }
            
            if (plan.learning_analysis.personalized_tips) {
                html += `<p><strong>Tips:</strong> ${plan.learning_analysis.personalized_tips}</p>`;
            }
            
            html += '</div>';
        }

        // Schedule Section
        if (plan.schedule && plan.schedule.schedule && plan.schedule.schedule.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>📅 Study Schedule (First 7 Days)</h4>
            `;
            
            plan.schedule.schedule.slice(0, 7).forEach(day => {
                html += `
                    <div style="margin-bottom: 1rem;">
                        <strong>Day ${day.day}</strong> ${day.date ? `(${day.date})` : ''}
                `;
                
                if (day.sessions && day.sessions.length > 0) {
                    html += '<ul>';
                    day.sessions.forEach(session => {
                        html += `<li><strong>${session.time || 'Time TBD'}:</strong> ${session.topic || 'Topic'}`;
                        
                        if (session.activities && session.activities.length > 0) {
                            html += ` - ${session.activities.join(', ')}`;
                        }
                        
                        html += '</li>';
                    });
                    html += '</ul>';
                } else {
                    html += '<p><em>No sessions scheduled</em></p>';
                }
                
                if (day.notes) {
                    html += `<p><em>Note: ${day.notes}</em></p>`;
                }
                
                html += '</div>';
            });
            
            if (plan.schedule.schedule.length > 7) {
                html += `<p><em>...and ${plan.schedule.schedule.length - 7} more days</em></p>`;
            }
            
            html += '</div>';
        }

        // Resources Section
        if (plan.resources && plan.resources.resource_recommendations && plan.resources.resource_recommendations.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>📖 Recommended Resources</h4>
            `;
            
            plan.resources.resource_recommendations.slice(0, 5).forEach(rec => {
                html += `<div style="margin-bottom: 1rem;"><strong>${rec.topic}:</strong>`;
                
                if (rec.resources && rec.resources.length > 0) {
                    html += '<ul>';
                    rec.resources.forEach(res => {
                        html += `<li><strong>${res.name}</strong> (${res.type})`;
                        if (res.description) {
                            html += ` - ${res.description}`;
                        }
                        html += '</li>';
                    });
                    html += '</ul>';
                } else {
                    html += '<p><em>No specific resources listed</em></p>';
                }
                
                html += '</div>';
            });
            
            html += '</div>';
        }

        // Progress Tracking Section
        if (plan.progress_tracking && plan.progress_tracking.checkpoint_schedule && plan.progress_tracking.checkpoint_schedule.length > 0) {
            html += `
                <div class="detail-section">
                    <h4>📈 Progress Checkpoints</h4>
                    <ul>
            `;
            
            plan.progress_tracking.checkpoint_schedule.forEach(cp => {
                html += `<li><strong>Day ${cp.day}:</strong> ${cp.checkpoint}`;
                if (cp.assessment) {
                    html += ` - ${cp.assessment}`;
                }
                html += '</li>';
            });
            
            html += '</ul>';
            
            if (plan.progress_tracking.tracking_metrics && plan.progress_tracking.tracking_metrics.length > 0) {
                html += '<p><strong>Track these metrics:</strong></p><ul>';
                plan.progress_tracking.tracking_metrics.forEach(metric => {
                    if (typeof metric === 'string') {
                        html += `<li>${metric}</li>`;
                    }
                });
                html += '</ul>';
            }
            
            html += '</div>';
        }

        // If no content was added, show message
        if (!html) {
            html = '<p>No detailed information available. Please try generating the plan again.</p>';
        }

        document.getElementById('details-content').innerHTML = html;

    } catch (error) {
        console.error('[Details] Error:', error);
        showToast(`❌ Error loading details: ${error.message}`, 'error');
        document.getElementById('details-content').innerHTML = `<p class="error">Error loading plan details: ${error.message}</p>`;
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Study Plan Generator initialized');
    console.log('🤖 AI Agents ready:');
    console.log('  1. Syllabus Analyzer');
    console.log('  2. Schedule Architect');
    console.log('  3. Resource Recommender');
    
    // Ensure home screen is visible on load
    document.getElementById('home-screen').classList.add('active');
});