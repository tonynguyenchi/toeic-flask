// TOEIC Audio Controller
class TOEICAudio {
    constructor() {
        this.currentAudio = null;
        this.audioInstances = new Map();
        this.isListeningPart = false;
        this.allowReplay = true; // Set based on exam mode (practice vs. actual)
        
        this.initializeAudio();
        this.bindEvents();
    }

    initializeAudio() {
        // Initialize sample audio on home page
        const sampleAudio = document.getElementById('sampleAudio');
        if (sampleAudio) {
            this.setupSampleAudio(sampleAudio);
        }

        // Initialize question audios on exam page
        document.querySelectorAll('.question-audio').forEach(audio => {
            this.setupQuestionAudio(audio);
        });
    }

    setupSampleAudio(audioElement) {
        const playBtn = document.getElementById('playAudioBtn');
        const progressBar = document.getElementById('audioProgressBar');
        const timeDisplay = document.getElementById('audioTime');
        const durationDisplay = document.getElementById('audioDuration');

        audioElement.addEventListener('loadedmetadata', () => {
            if (durationDisplay) {
                durationDisplay.textContent = this.formatTime(audioElement.duration);
            }
        });

        audioElement.addEventListener('timeupdate', () => {
            if (progressBar && timeDisplay) {
                const progress = (audioElement.currentTime / audioElement.duration) * 100;
                progressBar.style.width = `${progress}%`;
                timeDisplay.textContent = this.formatTime(audioElement.currentTime);
            }
        });

        audioElement.addEventListener('ended', () => {
            if (playBtn) {
                playBtn.innerHTML = '<i class="fas fa-play me-2"></i>Play Sample Audio';
                playBtn.classList.remove('btn-danger');
                playBtn.classList.add('btn-outline-primary');
            }
            if (progressBar) {
                progressBar.style.width = '0%';
            }
        });

        if (playBtn) {
            playBtn.addEventListener('click', () => {
                this.toggleSampleAudio(audioElement, playBtn);
            });
        }
    }

    setupQuestionAudio(audioElement) {
        const questionNumber = audioElement.dataset.question;
        this.audioInstances.set(questionNumber, audioElement);

        // Audio event listeners
        audioElement.addEventListener('loadstart', () => {
            this.showAudioLoading(questionNumber);
        });

        audioElement.addEventListener('canplaythrough', () => {
            this.hideAudioLoading(questionNumber);
        });

        audioElement.addEventListener('play', () => {
            this.onAudioPlay(questionNumber);
        });

        audioElement.addEventListener('pause', () => {
            this.onAudioPause(questionNumber);
        });

        audioElement.addEventListener('ended', () => {
            this.onAudioEnded(questionNumber);
        });

        audioElement.addEventListener('error', (e) => {
            this.onAudioError(questionNumber, e);
        });
    }

    bindEvents() {
        // Audio play buttons
        document.querySelectorAll('.audio-play-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const questionNumber = e.target.closest('[data-question]').dataset.question;
                this.playQuestionAudio(questionNumber);
            });
        });

        // Audio pause buttons  
        document.querySelectorAll('.audio-pause-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const questionNumber = e.target.closest('[data-question]').dataset.question;
                this.pauseQuestionAudio(questionNumber);
            });
        });
    }

    toggleSampleAudio(audioElement, playBtn) {
        if (audioElement.paused) {
            // Stop any currently playing audio
            this.stopAllAudio();
            
            audioElement.play().then(() => {
                playBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Audio';
                playBtn.classList.remove('btn-outline-primary');
                playBtn.classList.add('btn-danger');
                this.currentAudio = audioElement;
            }).catch(error => {
                console.error('Error playing sample audio:', error);
                this.showAudioError('sample');
            });
        } else {
            audioElement.pause();
            audioElement.currentTime = 0;
            playBtn.innerHTML = '<i class="fas fa-play me-2"></i>Play Sample Audio';
            playBtn.classList.remove('btn-danger');
            playBtn.classList.add('btn-outline-primary');
            this.currentAudio = null;
        }
    }

    playQuestionAudio(questionNumber) {
        const audioElement = this.audioInstances.get(questionNumber);
        if (!audioElement) {
            console.error(`Audio not found for question ${questionNumber}`);
            return;
        }

        // Stop any currently playing audio
        this.stopAllAudio();

        // Check if replay is allowed (for listening parts in strict mode)
        if (!this.allowReplay && audioElement.currentTime > 0) {
            this.showReplayNotAllowed(questionNumber);
            return;
        }

        audioElement.play().then(() => {
            this.currentAudio = audioElement;
            this.updateAudioVisualization(questionNumber, true);
        }).catch(error => {
            console.error(`Error playing audio for question ${questionNumber}:`, error);
            this.showAudioError(questionNumber);
        });
    }

    pauseQuestionAudio(questionNumber) {
        const audioElement = this.audioInstances.get(questionNumber);
        if (audioElement && !audioElement.paused) {
            audioElement.pause();
        }
    }

    stopAllAudio() {
        // Stop any currently playing audio
        if (this.currentAudio && !this.currentAudio.paused) {
            this.currentAudio.pause();
        }

        // Stop all question audios
        this.audioInstances.forEach(audio => {
            if (!audio.paused) {
                audio.pause();
            }
        });

        // Stop sample audio
        const sampleAudio = document.getElementById('sampleAudio');
        if (sampleAudio && !sampleAudio.paused) {
            sampleAudio.pause();
        }

        this.currentAudio = null;
    }

    onAudioPlay(questionNumber) {
        const playBtn = document.querySelector(`.audio-play-btn[data-question="${questionNumber}"]`);
        const pauseBtn = document.querySelector(`.audio-pause-btn[data-question="${questionNumber}"]`);

        if (playBtn && pauseBtn) {
            playBtn.classList.add('d-none');
            pauseBtn.classList.remove('d-none');
        }

        // Add visual feedback
        this.updateAudioVisualization(questionNumber, true);
    }

    onAudioPause(questionNumber) {
        const playBtn = document.querySelector(`.audio-play-btn[data-question="${questionNumber}"]`);
        const pauseBtn = document.querySelector(`.audio-pause-btn[data-question="${questionNumber}"]`);

        if (playBtn && pauseBtn) {
            pauseBtn.classList.add('d-none');
            playBtn.classList.remove('d-none');
        }

        this.updateAudioVisualization(questionNumber, false);
    }

    onAudioEnded(questionNumber) {
        this.onAudioPause(questionNumber);
        this.currentAudio = null;
        
        // Auto-advance to next question in listening parts (optional)
        if (this.isListeningPart) {
            this.autoAdvanceToNextQuestion(questionNumber);
        }
    }

    onAudioError(questionNumber, error) {
        console.error(`Audio error for question ${questionNumber}:`, error);
        this.showAudioError(questionNumber);
    }

    updateAudioVisualization(questionNumber, isPlaying) {
        const questionBlock = document.getElementById(`question-${questionNumber}`);
        const audioSection = questionBlock?.querySelector('.audio-section');
        
        if (audioSection) {
            if (isPlaying) {
                audioSection.classList.add('audio-playing');
                this.createAudioBars(audioSection);
            } else {
                audioSection.classList.remove('audio-playing');
                this.removeAudioBars(audioSection);
            }
        }
    }

    createAudioBars(container) {
        // Remove existing bars
        this.removeAudioBars(container);

        // Create audio visualization
        const visualizer = document.createElement('div');
        visualizer.className = 'audio-visualizer';
        
        const barsContainer = document.createElement('div');
        barsContainer.className = 'audio-bars';

        // Create animated bars
        for (let i = 0; i < 20; i++) {
            const bar = document.createElement('div');
            bar.className = 'audio-bar active';
            bar.style.animationDelay = `${i * 0.1}s`;
            barsContainer.appendChild(bar);
        }

        visualizer.appendChild(barsContainer);
        container.appendChild(visualizer);
    }

    removeAudioBars(container) {
        const existingVisualizer = container.querySelector('.audio-visualizer');
        if (existingVisualizer) {
            existingVisualizer.remove();
        }
    }

    showAudioLoading(questionNumber) {
        const playBtn = document.querySelector(`.audio-play-btn[data-question="${questionNumber}"]`);
        if (playBtn) {
            playBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            playBtn.disabled = true;
        }
    }

    hideAudioLoading(questionNumber) {
        const playBtn = document.querySelector(`.audio-play-btn[data-question="${questionNumber}"]`);
        if (playBtn) {
            playBtn.innerHTML = '<i class="fas fa-play me-2"></i>Play Audio';
            playBtn.disabled = false;
        }
    }

    showAudioError(questionNumber) {
        const questionBlock = document.getElementById(`question-${questionNumber}`) || document.body;
        
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger alert-dismissible fade show mt-2';
        errorAlert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            Audio failed to load. Please check your connection and try again.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        questionBlock.appendChild(errorAlert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorAlert.parentNode) {
                errorAlert.remove();
            }
        }, 5000);
    }

    showReplayNotAllowed(questionNumber) {
        const questionBlock = document.getElementById(`question-${questionNumber}`);
        
        const warningAlert = document.createElement('div');
        warningAlert.className = 'alert alert-warning alert-dismissible fade show mt-2';
        warningAlert.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Audio replay is not allowed in exam mode.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        questionBlock.appendChild(warningAlert);
        
        setTimeout(() => {
            if (warningAlert.parentNode) {
                warningAlert.remove();
            }
        }, 3000);
    }

    autoAdvanceToNextQuestion(currentQuestion) {
        // Auto-advance logic for listening parts (optional feature)
        const nextQuestion = parseInt(currentQuestion) + 1;
        const nextQuestionElement = document.getElementById(`question-${nextQuestion}`);
        
        if (nextQuestionElement) {
            setTimeout(() => {
                nextQuestionElement.scrollIntoView({ behavior: 'smooth' });
            }, 1000);
        }
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    // Set exam mode (practice vs. strict)
    setExamMode(mode) {
        this.allowReplay = mode === 'practice';
    }

    // Preload all audio files
    preloadAudio() {
        this.audioInstances.forEach(audio => {
            audio.load();
        });
    }

    // Get audio duration for a question
    getAudioDuration(questionNumber) {
        const audio = this.audioInstances.get(questionNumber);
        return audio ? audio.duration : 0;
    }

    // Check if audio is supported
    isAudioSupported() {
        const audio = document.createElement('audio');
        return !!(audio.canPlayType && audio.canPlayType('audio/mpeg').replace(/no/, ''));
    }
}

// Initialize audio controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.toeicAudio = new TOEICAudio();
    
    // Check audio support
    if (!window.toeicAudio.isAudioSupported()) {
        console.warn('Audio not supported in this browser');
        
        // Show warning to user
        const warningAlert = document.createElement('div');
        warningAlert.className = 'alert alert-warning alert-dismissible fade show';
        warningAlert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Audio Warning:</strong> Your browser may not support audio playback. 
            Please ensure you're using a modern browser for the best experience.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.container, .container-fluid')?.prepend(warningAlert);
    }
});

// Handle audio when user switches tabs
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.toeicAudio) {
        // Pause audio when tab is hidden (optional)
        console.log('Tab hidden - audio continues playing');
    }
});
