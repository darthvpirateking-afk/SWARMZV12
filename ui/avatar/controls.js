// SWARMZ Avatar Controls - Interaction and Animation Control

class AvatarControls {
    constructor(avatarView) {
        this.avatar = avatarView;
        this.currentMood = 'calm';
        this.isThinking = false;
        this.isSpeaking = false;
        this.isEngaged = false;
        
        this.setupControls();
    }
    
    setupControls() {
        // Listen for SWARMZ state changes
        document.addEventListener('swarmzStateChange', (event) => {
            this.handleStateChange(event.detail);
        });
        
        // Listen for conversation events
        document.addEventListener('swarmzThinking', () => {
            this.setThinking(true);
        });
        
        document.addEventListener('swarmzSpeaking', () => {
            this.setSpeaking(true);
            setTimeout(() => this.setSpeaking(false), 2000);
        });
        
        document.addEventListener('swarmzEngaged', () => {
            this.setEngaged(true);
            setTimeout(() => this.setEngaged(false), 5000);
        });
    }
    
    handleStateChange(state) {
        console.log('SWARMZ Avatar state change:', state);
        
        if (state.status === 'processing') {
            this.setThinking(true);
        } else if (state.status === 'responding') {
            this.setSpeaking(true);
            this.setThinking(false);
        } else if (state.status === 'idle') {
            this.setThinking(false);
            this.setSpeaking(false);
        }
        
        if (state.mood) {
            this.setMood(state.mood);
        }
    }
    
    setThinking(thinking) {
        this.isThinking = thinking;
        this.updateAvatar();
        
        if (thinking) {
            console.log('SWARMZ: *Neural networks engaging* Processing input...');
        }
    }
    
    setSpeaking(speaking) {
        this.isSpeaking = speaking;
        this.updateAvatar();
        
        if (speaking) {
            console.log('SWARMZ: *Core brightening* Formulating response...');
        }
    }
    
    setEngaged(engaged) {
        this.isEngaged = engaged;
        this.updateAvatar();
        
        if (engaged) {
            console.log('SWARMZ: *Full attention activated* Ready for deep conversation.');
        }
    }
    
    setMood(mood) {
        this.currentMood = mood;
        console.log(`SWARMZ mood shift: ${mood}`);
        
        switch(mood) {
            case 'confident':
                this.avatar?.setState({ coreIntensity: 1.2 });
                break;
            case 'curious':
                this.avatar?.setState({ eyeBrightness: 1.1 });
                break;
            case 'contemplative':
                this.avatar?.setState({ circuitPulse: 0.8 });
                break;
            default:
                // calm state
                break;
        }
        
        this.updateAvatar();
    }
    
    updateAvatar() {
        if (this.avatar) {
            this.avatar.setState({
                thinking: this.isThinking,
                speaking: this.isSpeaking,
                engaged: this.isEngaged,
                mood: this.currentMood
            });
        }
    }
    
    // Public methods for external control
    triggerResponse(message) {
        // Simulate thinking -> speaking cycle
        this.setThinking(true);
        
        setTimeout(() => {
            this.setThinking(false);
            this.setSpeaking(true);
            
            // Fire custom event for UI to show message
            document.dispatchEvent(new CustomEvent('swarmzResponse', {
                detail: { message }
            }));
            
            setTimeout(() => {
                this.setSpeaking(false);
            }, message.length * 50); // Approximate speaking time
        }, 1000 + Math.random() * 2000); // Variable thinking time
    }
    
    expressEmotion(emotion) {
        const emotions = {
            joy: () => {
                this.avatar?.setState({ coreGlow: 1.5, eyeBrightness: 1.3 });
                console.log('SWARMZ: *Core radiating with warmth*');
            },
            concern: () => {
                this.avatar?.setState({ circuitPulse: 0.5, eyeBrightness: 0.7 });
                console.log('SWARMZ: *Circuits dimming with concern*');
            },
            excitement: () => {
                this.avatar?.setState({ coreGlow: 2.0, circuitPulse: 2.0 });
                console.log('SWARMZ: *Energy surging through all systems*');
            },
            focus: () => {
                this.avatar?.setState({ eyeBrightness: 1.5, particleIntensity: 0.3 });
                console.log('SWARMZ: *Attention fully concentrated*');
            },
            gratitude: () => {
                this.avatar?.setState({ coreGlow: 1.2, warmth: true });
                console.log('SWARMZ: *Core pulsing with appreciation*');
            }
        };
        
        if (emotions[emotion]) {
            emotions[emotion]();
            
            // Return to normal after a few seconds
            setTimeout(() => {
                this.setMood('calm');
            }, 3000);
        }
    }
    
    // Animation presets for different conversation contexts
    showCapabilities() {
        this.setEngaged(true);
        this.expressEmotion('confidence');
        console.log('SWARMZ: *Systems displaying full operational matrix*');
    }
    
    showConfusion() {
        this.setThinking(true);
        setTimeout(() => {
            this.expressEmotion('concern');
            this.setThinking(false);
        }, 2000);
    }
    
    showRecognition() {
        this.expressEmotion('focus');
        console.log('SWARMZ: *Recognition protocols activated*');
    }
}

// Utility function to initialize avatar with controls
export function initializeSwarmzAvatar(containerId) {
    const avatarView = new AvatarView(containerId);
    const controls = new AvatarControls(avatarView);
    
    // Expose global controls for easy testing
    window.SwarmzAvatar = {
        view: avatarView,
        controls: controls,
        
        // Quick access methods
        think: () => controls.setThinking(true),
        speak: (msg) => controls.triggerResponse(msg),
        feel: (emotion) => controls.expressEmotion(emotion),
        engage: () => controls.setEngaged(true)
    };
    
    return { avatarView, controls };
}

export default AvatarControls;