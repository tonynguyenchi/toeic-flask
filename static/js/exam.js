// TOEIC Exam JavaScript Controller
class TOEICExam {
    constructor() {
        this.currentPart = 1;
        this.currentQuestion = 1;
        this.answers = {};
        this.attemptId = ATTEMPT_ID;
        this.saveTimeout = null;
        this.initializeExam();
        this.bindEvents();
        this.loadSavedAnswers();
    }

    initializeExam() {
        // Part ranges for TOEIC
        this.partRanges = {
            1: { start: 1, end: 10, name: 'Part I' },
            2: { start: 11, end: 40, name: 'Part II' },
            3: { start: 41, end: 70, name: 'Part III' },
            4: { start: 71, end: 100, name: 'Part IV' },
            5: { start: 101, end: 140, name: 'Part V' },
            6: { start: 141, end: 152, name: 'Part VI' },
            7: { start: 153, end: 200, name: 'Part VII' }
        };

        this.updateNavigator();
        this.updateProgress();
    }

    bindEvents() {
        // Part tab navigation (optional; template uses inline handlers)
        document.querySelectorAll('[data-part]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const partAttr = e.currentTarget.getAttribute('data-part');
                const part = parseInt(partAttr, 10);
                if (!Number.isNaN(part)) this.switchToPart(part);
            });
        });

        // Answer selection (content radios -> answer sheet) via event delegation
        document.addEventListener('change', (e) => {
            const target = e.target;
            if (target && target.matches('input[type="radio"][name^="question_"]')) {
                const questionNumber = parseInt(target.dataset.question);
                const answer = target.value;
                console.debug('[content->sheet] change', { questionNumber, answer });
                this.handleSelection(questionNumber, answer);
            }
        });

        // Answer sheet -> Content sync via event delegation
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.answer-btn');
            if (!btn) return;
            e.preventDefault();
            const questionNumber = parseInt(btn.dataset.question);
            const answer = btn.dataset.answer;
            console.debug('[sheet->content] click', { questionNumber, answer });
            this.handleSelection(questionNumber, answer);
        });

        // Question bubble navigation
        document.querySelectorAll('.question-bubble').forEach(bubble => {
            bubble.addEventListener('click', (e) => {
                const questionNumber = parseInt(e.target.dataset.question);
                this.goToQuestion(questionNumber);
            });
        });

        // Part navigation buttons
        const prevPartBtn = document.getElementById('prevPartBtn');
        if (prevPartBtn) {
            prevPartBtn.addEventListener('click', () => {
                if (this.currentPart > 1) {
                    this.switchToPart(this.currentPart - 1);
                }
            });
        }

        const nextPartBtn = document.getElementById('nextPartBtn');
        if (nextPartBtn) {
            nextPartBtn.addEventListener('click', () => {
                if (this.currentPart < 7) {
                    this.switchToPart(this.currentPart + 1);
                }
            });
        }

        // Navigator arrows
        const navPrevBtn = document.getElementById('navPrevBtn');
        if (navPrevBtn) {
            navPrevBtn.addEventListener('click', () => {
                if (this.currentPart > 1) {
                    this.switchToPart(this.currentPart - 1);
                }
            });
        }

        const navNextBtn = document.getElementById('navNextBtn');
        if (navNextBtn) {
            navNextBtn.addEventListener('click', () => {
                if (this.currentPart < 7) {
                    this.switchToPart(this.currentPart + 1);
                }
            });
        }

        // Submit exam
        const submitBtn = document.getElementById('submitExamBtn');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                if (typeof submitExam === 'function') {
                    submitExam();
                } else {
                    this.showSubmitConfirmation();
                }
            });
        }

        // Auto-save on page unload
        window.addEventListener('beforeunload', () => {
            this.saveAllAnswers();
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        if (this.currentPart > 1) this.switchToPart(this.currentPart - 1);
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        if (this.currentPart < 7) this.switchToPart(this.currentPart + 1);
                        break;
                }
            }
        });
    }

    switchToPart(partNumber) {
        // Hide current part
        const prevPartEl = document.getElementById(`part-${this.currentPart}`);
        if (prevPartEl) prevPartEl.style.display = 'none';
        const prevBubbles = document.getElementById(`bubbles-part-${this.currentPart}`);
        if (prevBubbles) prevBubbles.style.display = 'none';
        const prevTab = document.getElementById(`tab-part-${this.currentPart}`);
        if (prevTab) prevTab.classList.remove('active');

        // Show new part
        this.currentPart = partNumber;
        const curPartEl = document.getElementById(`part-${this.currentPart}`);
        if (curPartEl) curPartEl.style.display = 'block';
        const curBubbles = document.getElementById(`bubbles-part-${this.currentPart}`);
        if (curBubbles) curBubbles.style.display = 'block';
        const curTab = document.getElementById(`tab-part-${this.currentPart}`);
        if (curTab) curTab.classList.add('active');

        // Update navigator
        this.updateNavigator();
        this.updateNavigationButtons();

        // Scroll to first question of the part
        const firstQuestion = this.partRanges[this.currentPart].start;
        this.goToQuestion(firstQuestion);
    }

    goToQuestion(questionNumber) {
        const questionElement = document.getElementById(`question-${questionNumber}`);
        if (questionElement) {
            questionElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.currentQuestion = questionNumber;
            this.updateCurrentQuestionIndicator();
        }
    }

    saveAnswer(questionNumber, answer) {
        this.answers[questionNumber] = answer;
        this.updateQuestionBubble(questionNumber);
        this.updateProgress();
        
        // Debounced auto-save
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            this.saveToServer(questionNumber, answer);
        }, 300);
    }

    // Centralized handler to keep UI in sync no matter the source of selection
    handleSelection(questionNumber, answer) {
        // 1) Update content radio
        const radio = document.querySelector(`input[name="question_${questionNumber}"][value="${answer}"]`);
        if (radio && !radio.checked) {
            radio.checked = true;
        }

        // 2) Update answer sheet buttons
        const buttons = document.querySelectorAll(`.answer-btn[data-question="${questionNumber}"]`);
        buttons.forEach(btn => {
            if (btn.dataset.answer === answer) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-primary');
            } else {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-primary');
            }
        });

        // 3) Persist
        this.saveAnswer(questionNumber, answer);
    }

    async saveToServer(questionNumber, answer) {
        try {
            const formData = new FormData();
            formData.append('attempt_id', this.attemptId);
            formData.append('question_number', questionNumber);
            formData.append('answer', answer);

            const response = await fetch('/save_answer', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                this.showSaveIndicator();
            } else {
                console.error('Failed to save answer');
            }
        } catch (error) {
            console.error('Error saving answer:', error);
            this.showSaveError();
        }
    }

    updateQuestionBubble(questionNumber) {
        const bubble = document.getElementById(`bubble-${questionNumber}`);
        if (bubble) {
            bubble.classList.remove('unanswered');
            bubble.classList.add('answered');
        }
    }

    updateCurrentQuestionIndicator() {
        // Remove current indicator from all bubbles
        document.querySelectorAll('.question-bubble').forEach(bubble => {
            bubble.classList.remove('current');
        });

        // Add current indicator to current question
        const currentBubble = document.getElementById(`bubble-${this.currentQuestion}`);
        if (currentBubble) {
            currentBubble.classList.add('current');
        }
    }

    updateProgress() {
        const answeredCount = Object.keys(this.answers).length;
        const percentage = Math.round((answeredCount / 200) * 100);
        
        document.getElementById('progressText').textContent = `${answeredCount}/200 (${percentage}%)`;
        document.getElementById('progressBar').style.width = `${percentage}%`;
    }

    updateNavigator() {
        const navigatorTitle = document.getElementById('navigatorTitle');
        if (navigatorTitle) {
            navigatorTitle.textContent = this.partRanges[this.currentPart].name;
        }
    }

    updateNavigationButtons() {
        const prevBtn = document.getElementById('prevPartBtn');
        const nextBtn = document.getElementById('nextPartBtn');
        const navPrevBtn2 = document.getElementById('navPrevBtn');
        const navNextBtn2 = document.getElementById('navNextBtn');

        if (prevBtn) prevBtn.disabled = this.currentPart === 1;
        if (nextBtn) nextBtn.disabled = this.currentPart === 7;
        if (navPrevBtn2) navPrevBtn2.disabled = this.currentPart === 1;
        if (navNextBtn2) navNextBtn2.disabled = this.currentPart === 7;
    }

    showSubmitConfirmation() {
        const totalQuestions = 200;
        const answeredQuestions = Object.keys(this.answers).length;
        const unanswered = totalQuestions - answeredQuestions;

        document.getElementById('unansweredCount').textContent = unanswered;
        
        const submitModal = new bootstrap.Modal(document.getElementById('submitModal'));
        submitModal.show();
    }

    showSaveIndicator() {
        let indicator = document.getElementById('saveIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'saveIndicator';
            indicator.className = 'save-indicator';
            indicator.innerHTML = '<i class="fas fa-check me-1"></i>Saved';
            document.body.appendChild(indicator);
        }

        indicator.classList.add('show');
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 2000);
    }

    showSaveError() {
        let indicator = document.getElementById('saveErrorIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'saveErrorIndicator';
            indicator.className = 'save-indicator';
            indicator.style.background = 'var(--bs-danger)';
            indicator.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Save Failed';
            document.body.appendChild(indicator);
        }

        indicator.classList.add('show');
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 3000);
    }

    async loadSavedAnswers() {
        try {
            const response = await fetch(`/get_exam_state/${this.attemptId}`);
            const data = await response.json();

            if (data.answers) {
                this.answers = data.answers;
                
                // Restore radio button selections
                Object.entries(data.answers).forEach(([questionNumber, answer]) => {
                    const radio = document.querySelector(`input[name="question_${questionNumber}"][value="${answer}"]`);
                    if (radio) {
                        radio.checked = true;
                        this.updateQuestionBubble(parseInt(questionNumber));
                    }
                });

                this.updateProgress();
            }
        } catch (error) {
            console.error('Error loading saved answers:', error);
        }
    }

    saveAllAnswers() {
        // Force save all pending changes
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
            // Could implement a synchronous save here if needed
        }
    }
}

// Initialize exam when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.toeicExam = new TOEICExam();
});

// Intersection Observer for automatic question tracking
document.addEventListener('DOMContentLoaded', () => {
    const observerOptions = {
        root: null,
        rootMargin: '-50% 0px -50% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const questionElement = entry.target;
                const questionNumber = parseInt(questionElement.id.replace('question-', ''));
                if (window.toeicExam) {
                    window.toeicExam.currentQuestion = questionNumber;
                    window.toeicExam.updateCurrentQuestionIndicator();
                }
            }
        });
    }, observerOptions);

    // Observe all question blocks
    document.querySelectorAll('.question-block').forEach(block => {
        observer.observe(block);
    });
});
