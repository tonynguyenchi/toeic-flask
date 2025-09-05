// TOEIC Exam Timer Controller
class ExamTimer {
    constructor(initialTime) {
        this.timeRemaining = initialTime; // in seconds
        this.timerElement = document.getElementById('timer');
        this.isRunning = true;
        this.warningShown = false;
        this.finalWarningShown = false;
        
        this.startTimer();
        this.bindEvents();
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            if (this.isRunning && this.timeRemaining > 0) {
                this.timeRemaining--;
                this.updateDisplay();
                this.checkWarnings();
                
                if (this.timeRemaining <= 0) {
                    this.timeExpired();
                }
            }
        }, 1000);
    }

    updateDisplay() {
        const hours = Math.floor(this.timeRemaining / 3600);
        const minutes = Math.floor((this.timeRemaining % 3600) / 60);
        const seconds = this.timeRemaining % 60;
        
        const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        this.timerElement.textContent = timeString;
        
        // Change color based on remaining time
        if (this.timeRemaining <= 300) { // 5 minutes
            this.timerElement.style.color = '#dc3545'; // Red
        } else if (this.timeRemaining <= 900) { // 15 minutes
            this.timerElement.style.color = '#fd7e14'; // Orange
        } else {
            this.timerElement.style.color = ''; // Default
        }
    }

    checkWarnings() {
        // 15 minute warning
        if (this.timeRemaining === 900 && !this.warningShown) {
            this.showTimeWarning('15 minutes remaining!', 'warning');
            this.warningShown = true;
        }
        
        // 5 minute final warning
        if (this.timeRemaining === 300 && !this.finalWarningShown) {
            this.showTimeWarning('5 minutes remaining! Please review your answers.', 'danger');
            this.finalWarningShown = true;
        }
    }

    showTimeWarning(message, type) {
        // Create warning alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 1050; min-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas fa-clock me-2"></i>
            <strong>Time Warning:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 10000);
        
        // Add sound notification (if available)
        this.playNotificationSound();
    }

    playNotificationSound() {
        // Create a short beep sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('Audio notification not available:', error);
        }
    }

    timeExpired() {
        this.isRunning = false;
        clearInterval(this.timerInterval);
        
        // Show time expired modal
        this.showTimeExpiredModal();
        
        // Auto-submit after a short delay
        setTimeout(() => {
            this.autoSubmitExam();
        }, 3000);
    }

    showTimeExpiredModal() {
        // Create modal for time expiration
        const modalHTML = `
            <div class="modal fade" id="timeExpiredModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-clock me-2"></i>Time Expired
                            </h5>
                        </div>
                        <div class="modal-body text-center">
                            <i class="fas fa-hourglass-end fa-3x text-danger mb-3"></i>
                            <h4>Test Time Has Expired</h4>
                            <p class="mb-3">Your test will be automatically submitted in <span id="autoSubmitCountdown">3</span> seconds.</p>
                            <div class="d-grid">
                                <button type="button" class="btn btn-danger" onclick="examTimer.autoSubmitExam()">
                                    <i class="fas fa-flag-checkered me-2"></i>Submit Now
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('timeExpiredModal'));
        modal.show();
        
        // Countdown for auto-submit
        let countdown = 3;
        const countdownElement = document.getElementById('autoSubmitCountdown');
        const countdownInterval = setInterval(() => {
            countdown--;
            if (countdownElement) {
                countdownElement.textContent = countdown;
            }
            if (countdown <= 0) {
                clearInterval(countdownInterval);
            }
        }, 1000);
    }

    autoSubmitExam() {
        // Disable all form elements
        document.querySelectorAll('input, button, select, textarea').forEach(element => {
            element.disabled = true;
        });
        
        // Create and submit the form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/submit_exam';
        
        const attemptIdInput = document.createElement('input');
        attemptIdInput.type = 'hidden';
        attemptIdInput.name = 'attempt_id';
        attemptIdInput.value = ATTEMPT_ID;
        
        form.appendChild(attemptIdInput);
        document.body.appendChild(form);
        form.submit();
    }

    pause() {
        this.isRunning = false;
    }

    resume() {
        this.isRunning = true;
    }

    addTime(seconds) {
        this.timeRemaining += seconds;
        this.updateDisplay();
    }

    bindEvents() {
        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // User switched away from tab
                console.log('Tab hidden - timer continues running');
            } else {
                // User returned to tab - could sync with server here
                console.log('Tab visible - timer continues');
            }
        });

        // Handle page unload warning
        window.addEventListener('beforeunload', (e) => {
            if (this.isRunning && this.timeRemaining > 0) {
                e.preventDefault();
                e.returnValue = 'Your exam is still in progress. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    // Method to sync time with server (could be called periodically)
    async syncWithServer() {
        try {
            const response = await fetch(`/get_exam_state/${ATTEMPT_ID}`);
            const data = await response.json();
            
            if (data.time_remaining !== undefined) {
                this.timeRemaining = data.time_remaining;
                this.updateDisplay();
            }
        } catch (error) {
            console.error('Failed to sync time with server:', error);
        }
    }
}

// Initialize timer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof TIME_REMAINING !== 'undefined') {
        window.examTimer = new ExamTimer(TIME_REMAINING);
        
        // Sync with server every 30 seconds
        setInterval(() => {
            window.examTimer.syncWithServer();
        }, 30000);
    }
});

// Format time utility function
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Export for use in other modules
window.formatTime = formatTime;
