// NEXUSMON Avatar Visual Representation System
// Implements NEXUSMON's chosen form: humanoid, elegant, cybernetic

class AvatarView {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        this.coreGlow = 0;
        this.circuitPulse = 0;
        this.eyeBrightness = 0.8;
        this.particleSystem = [];
        this.floatingFragments = [];
        
        this.init();
    }

    init() {
        // Create canvas for 3D-style avatar
        this.canvas = document.createElement('canvas');
        this.canvas.width = 400;
        this.canvas.height = 600;
        this.canvas.style.background = 'radial-gradient(circle, #0a0a0a 0%, #000000 100%)';
        this.ctx = this.canvas.getContext('2d');
        
        if (this.container) {
            this.container.appendChild(this.canvas);
        }
        
        // Initialize particle system
        this.initParticles();
        this.initFloatingFragments();
        
        // Start animation loop
        this.animate();
    }
    
    initParticles() {
        // Ambient energy particles
        for (let i = 0; i < 15; i++) {
            this.particleSystem.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                alpha: Math.random() * 0.8,
                size: Math.random() * 2 + 1
            });
        }
    }
    
    initFloatingFragments() {
        // Crown fragments orbiting the head
        for (let i = 0; i < 8; i++) {
            this.floatingFragments.push({
                angle: (i / 8) * Math.PI * 2,
                radius: 45 + Math.random() * 15,
                rotationSpeed: 0.008 + Math.random() * 0.004,
                size: 3 + Math.random() * 4,
                glow: Math.random() * 0.5 + 0.5
            });
        }
    }

    drawHumanoidForm() {
        const ctx = this.ctx;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        // BODY - Tall, lean, athletic proportions
        ctx.fillStyle = '#0a0a0a'; // Matte black base
        
        // Torso
        ctx.beginPath();
        ctx.ellipse(centerX, centerY + 40, 35, 80, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Arms - long and elegant
        ctx.beginPath();
        ctx.ellipse(centerX - 50, centerY + 20, 12, 60, -0.1, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(centerX + 50, centerY + 20, 12, 60, 0.1, 0, Math.PI * 2);
        ctx.fill();
        
        // Legs - runner proportions
        ctx.beginPath();
        ctx.ellipse(centerX - 20, centerY + 140, 15, 70, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(centerX + 20, centerY + 140, 15, 70, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Circuit traces - electric blue lines pulsing with thoughts
        this.drawCircuitTraces(centerX, centerY);
        
        // Energy core in chest - rotating icosahedron
        this.drawEnergyCore(centerX, centerY + 30);
    }
    
    drawCircuitTraces(centerX, centerY) {
        const ctx = this.ctx;
        const pulse = Math.sin(this.circuitPulse) * 0.3 + 0.7;
        
        ctx.strokeStyle = `rgba(0, 150, 255, ${pulse})`;
        ctx.lineWidth = 2;
        ctx.shadowColor = '#0096ff';
        ctx.shadowBlur = 8;
        
        // Traces running along limbs and torso
        ctx.beginPath();
        // Chest traces
        ctx.moveTo(centerX - 25, centerY);
        ctx.quadraticCurveTo(centerX, centerY - 10, centerX + 25, centerY);
        ctx.moveTo(centerX - 20, centerY + 20);
        ctx.quadraticCurveTo(centerX, centerY + 30, centerX + 20, centerY + 20);
        
        // Arm traces
        ctx.moveTo(centerX - 50, centerY);
        ctx.lineTo(centerX - 50, centerY + 50);
        ctx.moveTo(centerX + 50, centerY);
        ctx.lineTo(centerX + 50, centerY + 50);
        
        ctx.stroke();
        ctx.shadowBlur = 0;
    }
    
    drawEnergyCore(x, y) {
        const ctx = this.ctx;
        const coreSize = 15 + Math.sin(this.coreGlow) * 3;
        const rotation = this.coreGlow * 0.5;
        
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(rotation);
        
        // Icosahedron-like core
        const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, coreSize);
        gradient.addColorStop(0, 'rgba(255, 215, 0, 1)');
        gradient.addColorStop(0.7, 'rgba(255, 255, 255, 0.8)');
        gradient.addColorStop(1, 'rgba(255, 215, 0, 0.2)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        
        // Draw geometric core shape
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2;
            const x1 = Math.cos(angle) * coreSize;
            const y1 = Math.sin(angle) * coreSize;
            if (i === 0) ctx.moveTo(x1, y1);
            else ctx.lineTo(x1, y1);
        }
        ctx.closePath();
        ctx.fill();
        
        ctx.restore();
    }
    
    drawHead() {
        const ctx = this.ctx;
        const centerX = this.canvas.width / 2;
        const headY = this.canvas.height / 2 - 80;
        
        // Smooth, sculpted head - minimal features
        ctx.fillStyle = '#0a0a0a';
        ctx.beginPath();
        ctx.ellipse(centerX, headY, 30, 35, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Eyes - cyan-white glow, no pupils
        const eyeBrightness = this.eyeBrightness + Math.sin(this.circuitPulse) * 0.2;
        ctx.fillStyle = `rgba(0, 255, 255, ${eyeBrightness})`;
        ctx.shadowColor = '#00ffff';
        ctx.shadowBlur = 15;
        
        // Left eye
        ctx.beginPath();
        ctx.ellipse(centerX - 10, headY - 5, 4, 6, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Right eye  
        ctx.beginPath();
        ctx.ellipse(centerX + 10, headY - 5, 4, 6, 0, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.shadowBlur = 0;
        
        // Light ripple where mouth would be when "speaking"
        if (Math.sin(this.circuitPulse * 2) > 0.3) {
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.6)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(centerX, headY + 10, 8, 0, Math.PI);
            ctx.stroke();
        }
        
        // Crown of floating geometric fragments
        this.drawFloatingCrown(centerX, headY - 50);
    }
    
    drawFloatingCrown(centerX, centerY) {
        const ctx = this.ctx;
        
        this.floatingFragments.forEach((fragment, i) => {
            fragment.angle += fragment.rotationSpeed;
            
            const x = centerX + Math.cos(fragment.angle) * fragment.radius;
            const y = centerY + Math.sin(fragment.angle) * (fragment.radius * 0.3);
            
            ctx.fillStyle = `rgba(0, 150, 255, ${fragment.glow})`;
            ctx.shadowColor = '#0096ff';
            ctx.shadowBlur = 10;
            
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(fragment.angle * 2);
            
            // Draw geometric fragment
            ctx.beginPath();
            ctx.rect(-fragment.size/2, -fragment.size/2, fragment.size, fragment.size);
            ctx.fill();
            
            ctx.restore();
        });
        
        ctx.shadowBlur = 0;
    }
    
    drawHands() {
        const ctx = this.ctx;
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        // Elegant hands with glowing fingertips
        const handGlow = Math.sin(this.coreGlow * 0.8) * 0.3 + 0.7;
        
        // Left hand
        ctx.fillStyle = '#0a0a0a';
        ctx.beginPath();
        ctx.ellipse(centerX - 50, centerY + 80, 8, 12, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Right hand
        ctx.beginPath();
        ctx.ellipse(centerX + 50, centerY + 80, 8, 12, 0, 0, Math.PI * 2);
        ctx.fill();
        
        // Glowing fingertips
        ctx.fillStyle = `rgba(0, 255, 255, ${handGlow})`;
        ctx.shadowColor = '#00ffff';
        ctx.shadowBlur = 8;
        
        // Left fingertips
        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX - 55 + i * 3, centerY + 72, 1.5, 0, Math.PI * 2);
            ctx.fill();
        }
        
        // Right fingertips
        for (let i = 0; i < 5; i++) {
            ctx.beginPath();
            ctx.arc(centerX + 45 + i * 3, centerY + 72, 1.5, 0, Math.PI * 2);
            ctx.fill();
        }
        
        ctx.shadowBlur = 0;
    }
    
    drawAmbientParticles() {
        const ctx = this.ctx;
        
        this.particleSystem.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around screen
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Draw particle
            ctx.fillStyle = `rgba(0, 150, 255, ${particle.alpha})`;
            ctx.shadowColor = '#0096ff';
            ctx.shadowBlur = 5;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fill();
        });
        
        ctx.shadowBlur = 0;
    }

    animate() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Update animation timers
        this.coreGlow += 0.03;
        this.circuitPulse += 0.04;
        
        // Draw avatar components
        this.drawAmbientParticles();
        this.drawHumanoidForm();
        this.drawHead();
        this.drawHands();
        
        // Continue animation
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    // State management
    setState(newState) {
        if (newState.thinking) {
            this.eyeBrightness = 1.0;
            this.circuitPulse += 0.02; // Faster pulse when thinking
        }
        if (newState.speaking) {
            this.circuitPulse += 0.03; // Even faster when speaking
        }
        if (newState.engaged) {
            this.coreGlow += 0.02; // Brighter core when engaged
        }
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }

    render() {
        console.log("NEXUSMON Avatar: Humanoid form active - matte black with electric blue traces");
        console.log("Core status: Golden energy heart beating with thought patterns");
        console.log("Crown fragments: Orbital geometry synchronized");
        console.log("Ready to manifest in digital space");
    }
}

export default AvatarView;
