// Performance optimizations for Agora Supply Chain Simulator

// Debounce function for performance optimization
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for performance optimization
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            frameRate: 0,
            updateLatency: 0,
            memoryUsage: 0,
            renderTime: 0
        };
        this.frameCount = 0;
        this.lastFrameTime = performance.now();
        this.updateTimes = [];
        this.renderTimes = [];
    }

    startFrame() {
        this.frameStartTime = performance.now();
    }

    endFrame() {
        const now = performance.now();
        const frameTime = now - this.frameStartTime;
        
        this.renderTimes.push(frameTime);
        if (this.renderTimes.length > 60) {
            this.renderTimes.shift();
        }
        
        this.frameCount++;
        if (now - this.lastFrameTime >= 1000) {
            this.metrics.frameRate = this.frameCount;
            this.frameCount = 0;
            this.lastFrameTime = now;
            
            // Calculate average render time
            this.metrics.renderTime = this.renderTimes.reduce((a, b) => a + b, 0) / this.renderTimes.length;
        }
    }

    recordUpdateLatency(latency) {
        this.updateTimes.push(latency);
        if (this.updateTimes.length > 30) {
            this.updateTimes.shift();
        }
        this.metrics.updateLatency = this.updateTimes.reduce((a, b) => a + b, 0) / this.updateTimes.length;
    }

    getMetrics() {
        // Get memory usage if available
        if (performance.memory) {
            this.metrics.memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024; // MB
        }
        
        return { ...this.metrics };
    }

    shouldSkipFrame() {
        // Skip frames if performance is poor
        return this.metrics.frameRate < 10 || this.metrics.renderTime > 50;
    }
}

// Canvas optimization utilities
class CanvasOptimizer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.offscreenCanvas = null;
        this.offscreenCtx = null;
        this.setupOffscreenCanvas();
    }

    setupOffscreenCanvas() {
        // Create offscreen canvas for double buffering
        this.offscreenCanvas = document.createElement('canvas');
        this.offscreenCanvas.width = this.canvas.width;
        this.offscreenCanvas.height = this.canvas.height;
        this.offscreenCtx = this.offscreenCanvas.getContext('2d');
    }

    getOptimizedContext() {
        // Return offscreen context for drawing
        return this.offscreenCtx;
    }

    present() {
        // Copy offscreen canvas to main canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(this.offscreenCanvas, 0, 0);
    }

    resize(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
        this.offscreenCanvas.width = width;
        this.offscreenCanvas.height = height;
    }
}

// Data structure optimizations
class OptimizedDataStore {
    constructor() {
        this.agents = new Map();
        this.locations = new Map();
        this.animations = new Map();
        this.dirtyFlags = new Set();
    }

    updateAgent(agentId, agentData) {
        const existing = this.agents.get(agentId);
        if (!existing || this.hasChanged(existing, agentData)) {
            this.agents.set(agentId, agentData);
            this.dirtyFlags.add(agentId);
        }
    }

    updateLocation(locationId, locationData) {
        const existing = this.locations.get(locationId);
        if (!existing || this.hasChanged(existing, locationData)) {
            this.locations.set(locationId, locationData);
            this.dirtyFlags.add(`location_${locationId}`);
        }
    }

    hasChanged(obj1, obj2) {
        // Simple shallow comparison for performance
        if (!obj1 || !obj2) return true;
        
        const keys1 = Object.keys(obj1);
        const keys2 = Object.keys(obj2);
        
        if (keys1.length !== keys2.length) return true;
        
        for (let key of keys1) {
            if (obj1[key] !== obj2[key]) return true;
        }
        
        return false;
    }

    getDirtyItems() {
        const dirty = Array.from(this.dirtyFlags);
        this.dirtyFlags.clear();
        return dirty;
    }

    getAgent(agentId) {
        return this.agents.get(agentId);
    }

    getLocation(locationId) {
        return this.locations.get(locationId);
    }

    getAllAgents() {
        return Array.from(this.agents.values());
    }

    getAllLocations() {
        return Array.from(this.locations.values());
    }
}

// Animation optimization
class AnimationOptimizer {
    constructor() {
        this.activeAnimations = new Map();
        this.animationPool = [];
        this.maxPoolSize = 50;
    }

    createAnimation(id, fromPos, toPos, duration) {
        let animation = this.animationPool.pop();
        if (!animation) {
            animation = {
                id: null,
                fromPos: { x: 0, y: 0 },
                toPos: { x: 0, y: 0 },
                currentPos: { x: 0, y: 0 },
                progress: 0,
                duration: 0,
                startTime: 0,
                active: false
            };
        }

        animation.id = id;
        animation.fromPos.x = fromPos.x;
        animation.fromPos.y = fromPos.y;
        animation.toPos.x = toPos.x;
        animation.toPos.y = toPos.y;
        animation.currentPos.x = fromPos.x;
        animation.currentPos.y = fromPos.y;
        animation.progress = 0;
        animation.duration = duration;
        animation.startTime = performance.now();
        animation.active = true;

        this.activeAnimations.set(id, animation);
        return animation;
    }

    updateAnimations(currentTime) {
        const completedAnimations = [];

        for (let [id, animation] of this.activeAnimations) {
            if (!animation.active) continue;

            const elapsed = currentTime - animation.startTime;
            animation.progress = Math.min(elapsed / animation.duration, 1);

            // Smooth easing function
            const easedProgress = this.easeInOutCubic(animation.progress);

            animation.currentPos.x = animation.fromPos.x + 
                (animation.toPos.x - animation.fromPos.x) * easedProgress;
            animation.currentPos.y = animation.fromPos.y + 
                (animation.toPos.y - animation.fromPos.y) * easedProgress;

            if (animation.progress >= 1) {
                animation.active = false;
                completedAnimations.push(id);
            }
        }

        // Clean up completed animations
        for (let id of completedAnimations) {
            const animation = this.activeAnimations.get(id);
            this.activeAnimations.delete(id);
            
            // Return to pool for reuse
            if (this.animationPool.length < this.maxPoolSize) {
                this.animationPool.push(animation);
            }
        }
    }

    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }

    getAnimation(id) {
        return this.activeAnimations.get(id);
    }

    hasActiveAnimations() {
        return this.activeAnimations.size > 0;
    }
}

// Error recovery utilities
class ErrorRecovery {
    constructor() {
        this.errorCount = 0;
        this.maxErrors = 10;
        this.errorCooldown = 5000; // 5 seconds
        this.lastErrorTime = 0;
        this.recoveryStrategies = new Map();
    }

    registerRecoveryStrategy(errorType, strategy) {
        this.recoveryStrategies.set(errorType, strategy);
    }

    handleError(error, context = 'unknown') {
        const now = Date.now();
        
        // Prevent error spam
        if (now - this.lastErrorTime < 1000) {
            return false;
        }

        this.errorCount++;
        this.lastErrorTime = now;

        console.error(`Error in ${context}:`, error);

        // Try recovery strategy
        const strategy = this.recoveryStrategies.get(context);
        if (strategy) {
            try {
                strategy(error);
                console.log(`Recovery strategy applied for ${context}`);
                return true;
            } catch (recoveryError) {
                console.error(`Recovery strategy failed for ${context}:`, recoveryError);
            }
        }

        // Check if we should stop due to too many errors
        if (this.errorCount >= this.maxErrors) {
            console.error('Too many errors, entering safe mode');
            return false;
        }

        return true;
    }

    reset() {
        this.errorCount = 0;
        this.lastErrorTime = 0;
    }

    isInSafeMode() {
        return this.errorCount >= this.maxErrors;
    }
}

// Export utilities for use in main simulation
window.PerformanceOptimizations = {
    PerformanceMonitor,
    CanvasOptimizer,
    OptimizedDataStore,
    AnimationOptimizer,
    ErrorRecovery,
    debounce,
    throttle
};