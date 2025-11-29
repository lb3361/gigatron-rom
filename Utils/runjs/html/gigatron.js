/**
 * @return {Uint8} a random Uint8
 * */
function randomUint8() {
    return Math.floor(Math.random() * 256);
}

/** Gigatron processor */
export class Gigatron {
    /** Create a Gigatron
     * @param {Object} options
     */
    constructor(options) {
        this.hz = options.hz || 6250000;
        this.rom = new Uint16Array(1 << (options.romAddressWidth || 16));
        this.romMask = this.rom.length - 1;
        this.ram = new Uint8Array(1 << (options.ramAddressWidth || 15));
        this.ramMask = this.ram.length - 1;
        this.reset();
        // randomize ram
        for (let i = 0; i < this.ram.length; i++) {
            this.ram[i] = randomUint8();
        }
    }

    /** reset registers to power-on state */
    reset() {
        this.pc = 0;
        this.nextpc = (this.pc + 1) & this.romMask;
        this.ac = 0;
        this.x = 0;
        this.y = 0;
        this.out = 0;
        this.outx = 0;
        this.inReg = 0xff; // active low!
        this.ctrl = 0x7c;
        this.bank = 0;
        this.prevctrl = -1;
        this.miso = 0;
    }

    /** advance simulation by one tick */
    tick() {
        let pc = this.pc;
        this.pc = this.nextpc;
        this.nextpc = (this.pc + 1) & this.romMask;
        this.prevctrl = -1;

        let ir = this.rom[pc];
        let d = (ir >> 0) & 0x00ff;
	switch ((ir >> 8) & 0x00ff) {

	case 0x5d: { // ora([Y,Xpp],OUT)
	    let addr = (this.y << 8) | this.x;
            this.x = (this.x + 1) & 0xff;
            this.writeOut(this.ac | this.readMem(addr))
	    break; }
	case 0x00: { // ld(d)
	    this.ac = d;
	    break; }
	case 0x01: { // ld([d])
	    this.ac = (this.ctrl & 1) ? this.miso : this.ram[d];
	    break; }
	case 0xc2: { // st([d])
	    this.ram[d] = this.ac;
	    break; }

	default: { // everything else
            let op = (ir >> 13) & 0x0007;
	    let mode = (ir >> 10) & 0x0007;
            let bus = (ir >> 8) & 0x0003;
            switch (op) {
            case 0: case 1: case 2:
            case 3: case 4: case 5:
                this.aluOp(op, mode, bus, d);
                break;
            case 6:
                this.storeOp(mode, bus, d);
                break;
            case 7:
                this.branchOp(mode, bus, d);
                break;
            }
	    break; }
	}
    }

    /** perform an alu op
     * @param {number} op
     * @param {number} mode
     * @param {number} bus
     * @param {number} d
     */
    aluOp(op, mode, bus, d)
    {
        let b = 0;
        switch (bus) {
            case 0:
                b = d;
                break;
            case 1:
                b = this.readMem(this.addr(mode, d));
                break;
            case 2:
                b = this.ac;
                break;
            case 3:
                b = this.inReg;
                break;
        }

        switch (op) {
            case 1:
                b = this.ac & b;
                break;
            case 2:
                b = this.ac | b;
                break;
            case 3:
                b = this.ac ^ b;
                break;
            case 4:
                b = (this.ac + b) & 0xff;
                break;
            case 5:
                b = (this.ac - b) & 0xff;
                break;
        }

        switch (mode) {
            case 0: case 1: case 2: case 3:
                this.ac = b;
                break;
            case 4:
                this.x = b;
                break;
            case 5:
                this.y = b;
                break;
            case 6: case 7:
                this.writeOut(b);
                break;
        }
    }

    /** perform a store op
     * @param {number} mode
     * @param {number} bus
     * @param {number} d
     */
    storeOp(mode, bus, d)
    {
        let b = 0;
        let w = 1;
        let addr = this.addr(mode, d);
        switch (bus) {
        case 0:
            b = d;
            break;
        case 1:
            if (this.ram.length <= 65536) {
                b = 0;
                console.error('UNDEFINED BEHAVIOR!');
            } else {
                this.prevctrl = this.ctrl;
                this.ctrl = addr & 0x80fd;
                this.bank = ((this.ctrl & 0xc0) << 9) ^ 0x8000;
                w = 0;
            }
            break;
        case 2:
            b = this.ac;
            break;
        case 3:
            b = this.inReg;
            break;
        }
        if (w) {
            if (addr & 0x8000) { addr = addr ^ this.bank; }
            this.ram[addr & this.ramMask] = b;
        }
        switch (mode) {
        case 4:
            this.x = this.ac;
            break;
        case 5:
            this.y = this.ac;
            break;
        }
    }

    /** perform a branch op
     * @param {number} mode
     * @param {number} bus
     * @param {number} d
     */
    branchOp(mode, bus, d) {
        const ZERO = 0x80;
        let c = true;
        let ac = this.ac ^ ZERO;
        let base = this.pc & 0xff00;

        switch (mode) {
            case 0: // jmp
                base = this.y << 8;
                break;
            case 1: // bgt
                c = ac > ZERO;
                break;
            case 2: // blt
                c = ac < ZERO;
                break;
            case 3: // bne
                c = ac != ZERO;
                break;
            case 4: // beq
                c = ac == ZERO;
                break;
            case 5: // bge
                c = ac >= ZERO;
                break;
            case 6: // ble
                c = ac <= ZERO;
                break;
            case 7: // bra
                c = true;
                break;
        }

        if (c) {
            let b = this.offset(bus, d);
            this.nextpc = base | b;
        }
    }

    /** calculate a ram address
     * @param {number} mode
     * @param {number} d
     * @return {number} the address
     */
    addr(mode, d) {
        switch (mode) {
            case 0:
            case 4:
            case 5:
            case 6:
                return d;
            case 1:
                return this.x;
            case 2:
                return (this.y << 8) | d;
            case 3:
                return (this.y << 8) | this.x;
            case 7:
                let addr = (this.y << 8) | this.x;
                this.x = (this.x + 1) & 0xff;
                return addr;
        }
    }

    /** read from memory with banking and spi
     * @param (number) addr
     */
    readMem(addr) {
	if (this.ctrl & 1) {
	    return this.miso;
	} else {
	    if (addr & 0x8000) { addr = addr ^ this.bank; }
	    return this.ram[addr & this.ramMask];
	}
    }

    /** write out register
     * @param (number) b
     */
    writeOut(b) {
        let rising = ~this.out & b;
        this.out = b;
        if (rising & 0x40) {
            // rising edge of out[6] registers outx from ac
            this.outx = this.ac;
        }
    }
    
    /** calculate a branch page offset
     * @param {number} bus
     * @param {number} d
     * @return {number} page offset
     */
    offset(bus, d) {
        switch (bus) {
            case 0:
                return d;
            case 1:
                return this.readMem(d);
            case 2:
                return this.ac;
            case 3:
                return this.inReg;
        }
    }
}
