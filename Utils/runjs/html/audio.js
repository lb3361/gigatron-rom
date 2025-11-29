const SAMPLES_PER_SECOND = 44100;

var AudioContext = window.AudioContext || window.webkitAudioContext;

/** Audio output */
export class Audio {
    /**
     * Create an Audio.
     * @param {Gigatron} cpu - The CPU
     */
    constructor(cpu, audiobits) {
        this.cpu = cpu;
        let context = this.context = new AudioContext();

        this.mute = false;
        this.volume = 0.33;
        this.cycle = 0;
        this.bias = 0;
        this.alpha = 0.99;
        this.scheduled = 0;
        this.full = false;
	this.audiobits = audiobits

        let numSamples = Math.floor(SAMPLES_PER_SECOND / 50);
        this.buffers = [];
        for (let i = 0; i < 8; i++) {
            let buffer = context.createBuffer(1,
                numSamples,
                SAMPLES_PER_SECOND);
            this.buffers.push(buffer);
        }
	let duration = this.buffers[0].duration;
        this.headBufferIndex = 0;
        this.tailBufferIndex = 0;
        this.headTime = this.tailTime = this.context.currentTime + 4*duration;
        this.channelData = this.buffers[0].getChannelData(0);
        this.sampleIndex = 0;
    }

    /** drain completed head buffers */
    drain() {
        let currentTime = this.context.currentTime;
        let headTime = this.headTime;
        let headBufferIndex = this.headBufferIndex;
        let scheduled = this.scheduled;
        let numBuffers = this.buffers.length;
        while (scheduled > 0 && headTime < currentTime) {
            headBufferIndex = headBufferIndex + 1;
	    if (headBufferIndex >= numBuffers)
		headBufferIndex = 0;
            headTime += this.buffers[headBufferIndex].duration;
            scheduled--;
        }
        this.headTime = headTime;
	this.headBufferIndex = headBufferIndex;
        this.scheduled = scheduled;
        this.full = scheduled == numBuffers;
	return currentTime;
    }

    /** flush current tail buffer */
    _flushChannelData() {
        let currentTime = this.drain();
        let context = this.context;
        let tailBufferIndex = this.tailBufferIndex;
        let buffer = this.buffers[tailBufferIndex];
        let scheduled = this.scheduled;
        let numBuffers = this.buffers.length;

        /* if the tail can't keep ahead of realtime, jump it to now */
        if (this.tailTime < currentTime) {
	    /* console.log('skip %o',currentTime - this.tailTime); */
            this.headTime = this.tailTime = currentTime + 3*buffer.duration;
            this.headBufferIndex = tailBufferIndex;
            scheduled = 0;
        }
        if (!this.mute) {
            let source = context.createBufferSource();
            source.buffer = buffer;
            source.connect(context.destination);
            source.start(this.tailTime);
        }
        scheduled++;
        this.tailTime += buffer.duration;
        tailBufferIndex = tailBufferIndex + 1;
	if (tailBufferIndex >= numBuffers)
            tailBufferIndex = 0;
        this.channelData = this.buffers[tailBufferIndex].getChannelData(0);
        this.tailBufferIndex = tailBufferIndex;
        this.scheduled = scheduled;
        this.full = scheduled == numBuffers;
	/* if (this.full) console.log('full'); */
        this.sampleIndex = 0;
    }

    /** advance simulation by one tick */
    tick() {
        this.cycle += SAMPLES_PER_SECOND;
        if (this.cycle >= this.cpu.hz) {
            this.cycle -= this.cpu.hz;
	    if (! this.full) {
		let sample;
		if (this.audiobits >= 8) {
		    sample = (this.cpu.outx >> 0) / 128;
		} else if (this.audiobits >= 6) {
		    sample = (this.cpu.outx >> 2) / 32;
		} else {
		    sample = (this.cpu.outx >> 4) / 8;
		}
		this.bias = (this.alpha * this.bias) + ((1 - this.alpha) * sample);
		sample = (sample - this.bias) * this.volume;
		this.channelData[this.sampleIndex++] = sample;
		if (this.sampleIndex == this.channelData.length)
                    this._flushChannelData();
            }
        }
    }
}
