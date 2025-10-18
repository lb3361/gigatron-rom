# DEV7ROM implementation tour

This document goes over the implementation *differences* between the Gigatron official ROMv6 and DEV7ROM. This is not easily achieved with diffs or pull requests because part of the ROM development process consists of moving the code in order to pack it optimally. Therefore, in order to make it easier to understand what has been changed, this document explains the changes with links pointing to the relevant parts of the code. It assumes some level of familarity with what DEV7ROM offers, either from the [forum](https://forum.gigatron.io/viewtopic.php?t=411&start=40) [threads](https://forum.gigatron.io/viewtopic.php?p=4168#p4168) or from the [`vCPU7.md`](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md) and [`GT1-compression.txt`](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/GT1-compression.txt) documentation files.


## 1. Build system

The main change here is the addition of *conditional compilation* directives that can be used in the [`Makefile`](https://github.com/lb3361/gigatron-rom/blob/doc/Makefile#L66) as follows

```makefile
dev128k7.rom: Core/* Apps/*/* Makefile interface.json
	python3 Core/dev.asm.py \
		-DDISPLAYNAME=\"[128k7]\"\
		-DWITH_128K_BOARD=1 \
		-DROMNAME=\"$@\" \
		${DEV7APPS}\
		SpiSd=Apps/More/system7.gt1z\
		Main=Apps/MainMenu/MainMenu_sd.gcl\
		Reset=Core/Reset.gcl
``` 

Here, the `ROMNAME` macro tells which file to write, the `WITH_128K_BOARD` macro tells to compile the `dev128k7.rom` variant which targets the Gigatron 128k and ensures that the screen buffer is always in memory bank 1 regardless of the memory bank selected for the vCPU. The `DISPLAYNAME` macro is passed to the GCL [`Reset.gcl`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L318) program that initializes the Gigatron and displays the ROM name on the screen.

Inside the [ROM source](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L179), conditions are declared with Python's function `defined` and used with normal Python `if` statements.
Conditional compilation is implemented in the last few lines of the [`asm.py`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/asm.py#L687-L706) file, which are already present in the ROMv6 repository but not used.

Conditionals are declared like this:
```python
# Enable patches for 128k board --
# Roms compiled with this option can only be used
# with a Gigatron equipped with a 128k extension board.
# ...
WITH_128K_BOARD = defined('WITH_128K_BOARD')
```
and used like this:
```python
st([entropy+1])
ld(1,Y)
if WITH_128K_BOARD:
  adda([Y,entropy2])            # displaced third entropy byte
  st([Y,entropy2])
else:
  adda([entropy+2])             # preserved third entropy byte
  st([entropy+2])
ld([vAC+1],Y)
ld([vAC+0])
adda(1)

```

The ROMv6 version of `asm.py` outputs a warning for certain [branch instructions that Marcel feared could misbehave](https://github.com/kervinck/gigatron-rom/issues/78) because of a long propagation delay in the Gigatron motherboard. Although this possibility was for me a [cause of concern](https://forum.gigatron.io/viewtopic.php?t=403)), no such malfunction has been observed after three years of extensive testing on a variety of gigatron builds. This warning code has been [changed](https://github.com/lb3361/gigatron-rom/blob/doc/Core/asm.py#L367-L378) to depend on a variable `warn` that more narrowly target the two [branch instructions at risk](https://github.com/lb3361/gigatron-rom/blob/doc/Core/asm.py#L78-L84) and is used to disable the warning in the finite state machine dispatcher (e.g. [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6579)). 

Compilation variable `DISPLAYNAME` (see Makefile fragment above) is used by the [`Reset.gcl`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L318) program to display the rom name. This is implemented by a ad hoc patch file [`gcl0x.py`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/gcl0x.py#L352-L353). A more general solution might be desirable.

The `Makefile` also contains a [few changes](https://github.com/lb3361/gigatron-rom/blob/doc/Makefile#L272-L292) related to GT1 compression, which shall be discussed later in this document. The [`dev.asm.py`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11946-L11957) code that parses the compilation command transparently supports  `.gcl`, `.gt1`, `.gt1z`, or `.py` files. However support for `.gtb` and `.rgb` files has been simplified. Instead we rely on the utility programs [`Utils/gtbtogt1.py`](https://github.com/lb3361/gigatron-rom/blob/doc/Utils/gtbtogt1.py) and [`Utils/imgtogt1.py`](https://github.com/lb3361/gigatron-rom/blob/doc/Utils/imgtogt1.py) to convert such files into compressible GT1 files.


## 2. ABI

The Gigatron application binary interface is traditionally defined by the file [`interface.json`](https://github.com/lb3361/gigatron-rom/blob/doc/interface.json) that defines symbols that are not expected to change in future official ROMS. New symbols are added when new official ROMs are released, with a suffix indicating which ROM version has introduced that symbol:

```json
 "videoTable"           : "0x0100",
 "vReset"               : "0x01f0",
 "vIRQ_v5"              : "0x01f6",
 "ctrlBits_v5"          : "0x01f8",
 "videoTop_v5"          : "0x01f9",
```

Since DEV7ROM is a development ROM, its ABI is further described in another JSON file, [`Core/interface-dev.json`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/interface-dev.json). This file mostly defines symbols containing suffix `_v7` because DEV7ROM was seen as steps towards ROMv7. Just like the main interface file, this file defines variable locations, SYS calls, and opcodes.


## 2. Memory map

The following table summarizes the contents of the DEV7ROM.
It is frequent during the development of a ROM to move vCPU implementations of SYS call implementations from one region to another in order to minimize the quantity of unused ROM space.



| Pg | Addresses | Contents 
-----| --------- | -------- 
| 0  | 0x0000-0x007f | Boot sequence. Soft Reset. 
|    | 0x0080-0x00ff | SYS call entry points.
| 1  | 0x0100-0x01ff | Video and audio loop (vertical blanking rows).
| 2  | 0x0200-0x02ff | Video and audio loop (visible rows).  
| 3  | 0x0300-0x03ff | Main vCPU opcode implementation and dispatch page.
| 4  | 0x0400-0x04a6 | vCPU opcode impl (many)
|    | 0x04a7-0x04ea | SYS calls (random,draw4,vdrawbits...)
|    | 0x04eb-0x04ff | vRTI return code.
| 5  | 0x0500-0x05ff | Right shift table.
| 6  | 0x0600-0x06ff | SYS calls (right shifts). Right shift return points. 
| 7  | 0x0700-0x07ff | Font (ASCII 32 to 81).
| 8  | 0x0800-0x08ff | Font (ASCII 82 to 126, Symbols 127 to 131).
| 9   | 0x0900-0x09ff | Note tables (C-0 to A#7).
| 10  | 0x0a00-0x0aff | Inversion table.
| 11  | 0x0b00-0x0bcc | SYS calls (setmode,setmemory,expander,spi,6502...)
|     | 0x0bcd-0x0bff | vCPU opcode impl (calli,cmph[su],peeka)
| 12 | 0x0c00-0x0cff | SYS calls (sprites)
| 13 | 0x0d00-0x0d8a | SYS call impl (expander,spi)
|    | 0x0d8b-0x0dff | v6502 (opcodes).
| 14 | 0x0e00-0x0eff | v6502 (decoder entry point, addressing modes).
| 15 | 0x0f00-0x0fff | v6502 (opcode dispatch table).
| 16 | 0x1000-0x10ff | v6502 (more opcodes).
| 17 | 0x1100-0x11ff | v6502 (secondary entry point, more opcodes). 
| 18 | 0x1200-0x1243 | Extended vertical blanking code.
|    | 0x1244-0x12ff | SYS call impl (vdrawbits,scanmem).
| 19 | 0x1300-0x13ff | SYS call impl (copy,copyext,mul,div).
| 20 | 0x1400-0x14ff | FSM code (mul,div).
| 21 | 0x1500-0x15ff | FSM code (microops, sysloader microcode).
| 22 | 0x1600-0x16ff | FSM code (sysexec microcode).
| 23 | 0x1700-0x17ff | vCPU prefix 35 opcode and dispatch.
| 24 | 0x1800-0x18ff | FSM code (copy,copyn,copys,movl,movf,exba).
| 25 | 0x1900-0x19ff | vCPU opcode impl (poke?,doke?,deek?,cmp??,addv,subv,moviw,jcc).
| 26 | 0x1a00-0x1aff | FSM code (subl,andl,orl,xorl,ldfac,ldfarg).
| 27 | 0x1b00-0x1bff | FSM code (addl,negx,notvl,negvl,lslvl,incvl,leeka,lokea).
| 28 | 0x1c00-0x1cff | FSM code (lsrxa,rorx,ldxw,stxw).
| 39 | 0x1d00-0x1dff | FSM code (macs,mulq).
| 30 | 0x1e00-0x1eff | FSM code (cmpl?,lslxa,stfac).
| 31 | 0x1f00-0x1fff | vCPU opcode impl (stack,stlac,ldlac,incv,negv,reset).
| 32 | 0x2000-0x2014 | LUP implementation and return
|    | 0x2015-0x2051 | SYS call impl (exec,unpack,ddab)
|    | 0x2052-0x20ff | vCPU opcode impl (subw,movw,movq?,ldxw,stxw,dbne,addsv).
| 33 | 0x2100-0x2127 | FSM code (addsv)
|    | 0x2128-0x2177 | Enhanced vIRQ code
|    | 0x2178-0x21ff | FSM code (vsave,vrestore)
| 34 | 0x2200-0x22ff | FSM code (ddab,fill)
| 35 | 0x2300-0x23ff | FSM code (blit)



## 3. Registers and variables

DEV7ROM introduces substantial changes to the page zero variables:

### 3.1. Registers

Space has been allocated for new vCPU registers, including a 16 bit extension `vSPH` of the stack pointer `vSP`, source and destination pointers `vT2` and `vT3` for copy iteration, an accumulator `vLAC` for 32 bits integers, which can become part of a floating point accumulator when used with bytes `vLAX`, `vFAE`, `vFAS` respectively containing a mantissa extension, a floating point exponent, and sign information. 

Except for the stack pointer extension `vSPH`, these registers occupy [the 0x81-0x8b region](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L424-L429) that follows the constant one at location `0x80`.
Variables named [`userVars2_vX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L430) have been introduced to clearly identify the beginning of the user available locations in the upper half of page zero. However, programs that only rely on the ROMv6 vCPU opcodes are free to use the locations affected to these registers. 

These changes are part of the DEV7ROM ABI and are exposed in [`Core/interface-dev.json`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/interface-dev.json#L10-L21) as follows:

```json
    "userVars_v7"          : "0x0036",
    "userVars2"            : "0x0081",
    "userVars2_v4"         : "0x0082",
    "userVars2_v5"         : "0x0081",
    "userVars2_v6"         : "0x0081",
    "vFAS_v7"              : "0x0081",
    "vFAE_v7"              : "0x0082",
    "vLAX_v7"              : "0x0083",
    "vLAC_v7"              : "0x0084",
    "vT2_v7"               : "0x0088",
    "vT3_v7"               : "0x008a",
    "userVars2_v7"         : "0x008c",
```

### 3.2. Relocations

The high stack pointer byte `vSPH` is located immediately after the normal stack pointer byte, effectively making the `vSP` register [16 bits long](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L355). Public names have been defined in the [`Core/interface-dev.json`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/interface-dev.json#L2-L4) file

```json
    "vSP_v7"      :  "0x001c",
    "vSPL_v7"     :  "0x001c",
    "vSPH_v7"     :  "0x001d",
```

This space was formerly used by the private variable `vTmp` which is used by the implementation of most vCPU opcodes. Instead, DEV7ROM relocates `vTmp` to the [former location](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L397) of the `ledTempo` variable which has been [displaced into page 1](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L445).

The displacement of the `ledTempo` variable is the only ABI change introduced by DEV7ROM. A new name `ledTempo_v7` has been defined in [`Core/interface-dev.json`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/interface-dev.json#L22), and the [`Core/Reset.gcl`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L11) file has been modified to set the initial LED tempo using the [relocated variable](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L304). The LED tempo in DEV7ROM is a little bit faster than ROMv6 in order to make it easy to recognize which ROM is running.

```json
    "ledTempo_v7"          : "0x01f3",
```

The original definition of variable `ledTempo` is still available in the [`interface.json`](https://github.com/lb3361/gigatron-rom/blob/doc/interface.json#L41) file in order to allow old programs to compile. Such programs might try to affect the LED tempo by writing into the old `ledTempo` location, with no effect whatsoever. Values stored into the old `ledTempo` location will be overwritten by the following vCPU instructions using this location as `vTmp`. This is minor because, since ROMv2, the [recommended way to manipulate the LEDs](https://github.com/lb3361/gigatron-rom/blob/doc/BASIC/LEDs.gtb) no longer relies on `ledTempo` but uses the `ledState_v2` variable at address `0x2e` (decimal 46) to stop the LED dance. 

Because DEV7ROM uses a shorter `vReset` code at address 0x1f0 (see later for an explanation of the `RESET_v7` instruction), [additional space](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L443-L447) has been made available in range 0x1f2-0x1f5. Besides the new location of `ledTempo`, this space has been used to relocate the private variable `ledTimer` and the third byte of the `entropy` variable (only when the conditional compilation switch `WITH_128K_BOARD` is defined.)  When `WITH_128K_BOARD` is defined, the former page 0 location of `ledTimer` and `entropy[2]` are used to hold copies of the control byte that defines the memory banking configuration that should be in effect [when generating the video signal](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L316-L320) or [when running vCPU instructions](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L387-L391).

The [ROM initialization code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L670-L675),  the [entropy generation code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1234-L1239), the [led sequencer](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1248-L1251) [code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1266-L1267), and the `SYS_Random` [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2995-L3000), have been modified to use the variables relocated in page 1 in place of their former page 0 versions. This is made easy by ensuring that the Y register contains 1 and changing the addressing mode of the native CPU instruction from, for instance, `ld([ledTempo])` to `ld([Y,ledTempo_v7])`.


## 4. vCPU changes

The initial goal of DEV7ROM was to provide a way to run a large program such as [MSCP](https://forum.gigatron.io/viewtopic.php?p=3617#p3617) on the 128K Gigatron. The 128KB of memory are divided in four 32KB banks. Address range `0x0000-0x7fff` always shows bank zero. Address range `0x8000-0xffff` shows any of the four banks according to bits 6 and 7 of the argument of the native `clrl` instruction. Since both the video loop and the vCPU see the same memory banks, the 64KB address space seen by the vCPU always contains the framebuffer. That does not leave enough space to run MSCP.  The solution was to have the ROM swap banks on the fly, using the selected bank when vCPU instructions are executed, but reverting to bank 1 when the ROM runs the video output code. To do this fast enough, one needs two page zero location to cache the control bits for both memory configuration. To find such locations some variables had to be moved to different locations. 

Hence came the idea to make space for these relocated variables by shortening the six bytes reset handler `vReset` at address 0x1f0. Instead of having it invoke a secret SYS call, we can use a secret vCPU opcode. And since there is no space in page 3 for such an instruction, we can extend the encoding of the conditional branch opcodes to provide new opcodes starting with prefix `0x35`.  So it all starts with the conditional branch opcodes.

### 4.1. Conditional branch opcodes

In ROMv6, all the conditional branches are implemented with a very intricate code entirely located in page 3. Essentially, this code jumps to the address indicated by the next opcode bytes to evaluate the condition, and, if true, reads the third opcode byte to decide where to jump.
In DEV7ROM this code is reduced to the [following code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2231-L2237) which simply jumps to the address indicated by the second opcode byte into page 23 which is now an implementation and dispatch page that is used whenever an opcode stats with byte 0x35. As for every page 3 opcode, the gigatron accumulator AC contains the second opcode byte. The first native instruction stores it back, but incrementing X. The next two native instructions jump to page 23, and the last one, which runs in the delay slot of the jump instruction, reloads the high program counter byte into Y in order to make is easy to access the third opcode byte if needed.

```python
# Instruction PREFIX35: (used to be BCC)
label('BCC')
label('PREFIX35')
st([Y,Xpp])                     #10
ld(hi('PREFIX35_PAGE'),Y)       #11
jmp(Y,AC)                       #12
ld([vPC+1],Y)                   #13
```

The rest now happens in page 23 
([`BEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7778-L7793),
[`BGT`, `BLT`, `BGE`, `BLE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7806-L7846), [`BNE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7871-L7886), and also [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7900-L7909).) 
Except for the fact that some of these entry points are very close to each other, there is much more space to implement the branch opcodes efficiently. In the end the new branch instructions are faster than the original ones.

However, as a result, plenty of space has been freed in both the main vCPU implementation page (page 3) and prefix `0x35` implementation page (page 23). The page 3 locations corresponding the condition byte of the branch instructions have been repurposed for new conditional branch instructions `Jcc` that accept two byte addresses and can cross page boundaries ([`JEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2264-L2270), [`JGT`, `JLT`, `JGE`, `JLE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2305-L2338), and [`JNE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2400-2407).) 
Since the page 3 code for these instructions merely contains jumps to their 
[actual implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8627-L8710), there was still plenty of space for new opcodes.

### 4.2. Reset sequence

Meanwhile a new instruction [`RESET`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7893-L7898) with prefix `0x35` implements the soft reset. This is a good opportunity to describe all the changes in the reset sequence.

* When the power is switched on, the Gigatron executes the [initialization code at ROM address zero](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L592-L731). This has changed very little since the early ROMS. It sets essential variables, writes the `vReset` handler at address `0x1f0`, initialized the vCPU program counter to `vReset`, and jumps into the video loop. In the DEV7ROM version, the `vReset` handler contains the `RESET` opcode, that is the prefix byte `0x35`, and the page 23 address of the `RESET` instruction, `0x7d`.

*  As soon as the video loop has spare time, it runs vCPU instructions and therefore executes the `RESET` opcode. The [`RESET`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7895-L7898) opcode jumps to its [actual implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10632-L10639) which self-restarts until having at least 88 cycles to execute, and otherwise jumps into a [soft reset routine](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L749-L786) which essentially replaces the secret reset SYS call of earlier ROMS. The secret reset SYS call code has been reordered to make it more compact. It also sets the [high stack pointer byte](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L752) to zero and sets the variables that define the video mode to values that depend on whether `WITH_128K_BOARD` or `WITH_512K_BOARD` are defined. Then it load and executes the [`Reset`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl) program. The DEV7ROM code achieves this by jumping directly into the implementation of `SYS_Exec` [after adjusting the tick counter](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L778-L786) to match instead of redispatching the `SYS` opcode of the `vReset` handler [as in earlier ROMs](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L716-L726).

*  The `Reset.gcl` program is very similar to that of ROMv6. The only differences are the ability to [detect a 512K Gigatron](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L250-L257), the aforementioned code to use `ledTempo_v7` instead of `ledTempo`, and [code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/Reset.gcl#L208-L225) that locates `CardBoot` and `MainMenu` using `SYS_ReadRomDir` and can act reasonably when `CardBoot` is not found. 


### 4.3. maxTicks

The constant `maxTicks` represents the half of the number of cycles needed to even consider scheduling a vCPU opcode execution. As of ROMv6, all official ROMs use `maxTicks=14` and therefore expect that, absent shenanigans, all vCPU opcode implementation must return within 28 cycles. DEV7ROM uses [`maxTicks=15`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L472) by DEV7ROM because it provides two additional cycles for implementing more ambitious vCPU instructions.

Using `maxTicks=15` has been [pionnered by at67](https://forum.gigatron.io/viewtopic.php?t=281&hilit=maxticks), this change has proven to be very useful and surprisingly problem free, with two notable exceptions:

* Changing `maxTicks` messes up the virtual IRQ code. This has in fact been fixed in ROMv6 [already](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L2430).
* Incrementing `maxTicks` changes the interpretation of the argument of the `SYS` vcpu opcode. Calling the `SYS` opcode with the same argument byte causes it to wait for an execution window that is two cycles longer than required. Alas this can be a problem when running [video mode zero](https://forum.gigatron.io/viewtopic.php?p=4115#p4115) because the longest vCPU window available during vertical blanking is 134 cycles long, just enough to run `SYS_VDrawBit` which is extensively used to display text. As explained in the post, this is fixed with by [shaving two cycles](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1410-L1455) in the vertical blanking part of the video loop. 

This means that the code implementing vCPU opcodes must return within 30 cycles instead of 28, making it possible, for instance, to displace the [`CALL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2605-2609) opcode [outside page 3.](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2937-2954).

It is still possible to implement vCPU opcode that wait for a longer execution window. For instance the [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10805-L10830) of the [`MOVW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2560-L2569) opcode needs 36 cycles. Therefore it explicitly [tests the duration of the available execution window](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10808-L10811) and [self-restarts](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10826-L10830) until it is long enough. Such longer opcode execution times [come with a hidden penalty](https://forum.gigatron.io/viewtopic.php?p=3648#p3648) because they are harder to schedule. It is therefore necessary to pay attention to the balance of gains and losses. For instance, one can schedule at most four `MOVW` opcodes in a typical vCPU execution slice, replacing four `LDW` and four `STW` opcodes. This works because the same time slice can only hold seven `LDW` or `STW` instructions. But if `MOVW` was merely two cycles longer, this systematic execution time gain would disappear. 

There are also hybrid situations. For instance the stack opcodes [`PUSH`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2409-L2414) and [`POP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2357-L2362) must manipulate the 16 bits page pointer. Their [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10379-L10457) first tests whether the operation will reach a page boundary and either executes a code that returns in less than 30 cycles, or a longer code that deals with the page crossing but stalls until having at least 38 cycles to run (an infrequent condition). Similarly the implementation of the [`STLW` and `LDLW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2682-L2694) opcodes [follow a slower code path](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10459-L10550) cycles when a 16 bits stack is active, that is, when `vSPH` is nonzero. This slower code path requires 36 or 38 cycles and therefore must stall until having a sufficient time window. Having `LDLW` wait for a 38 cycle window is still acceptable because it replaces a `LDI/ADDW/DEEK` combination that consumes a minimum of 16+28+28=72 cycles.

The [`ALLOC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2644-L2646) opcode also [checks whether a 16 bits stack is active](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10337-L10338). However it avoids timing complications because [both paths](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10339-L10364) complete in less than 30 cycles.


### 4.4. Opcodes

DEV7ROM implements a substantial number of additional vCPU opcodes. These opcodes are documented [here](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md). Many of these additional opcodes, and most certainly the most complex ones, use some of the `sysArgs[0:7]` bytes as working variables. In particular, variable `sysArg7` is used by all opcodes that rely on a finite state machine. This is always indicated in the [documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md) because it often means that these opcodes cannot be used to read or write the `sysArgs[0:7]` array, for instance to prepare a SYS call. 

As of ROMv6, all official gigatron ROMs implement or dispatch all vCPU opcodes from page 3. Although all conditional branch opcodes start with prefix `0x35`, their secondary bytes, which specifies the condition, is also dispatched in page 3. In contrast, DEV7ROM features two kind of vCPU opcodes, those that are dispatched in page 3, and those that start with prefix `0x35` and are dispatched in page 23.

We can also distinguish opcodes according to their implementation. Some are entirely implemented in the dispatch page to ensure speed. Others jump to their actual implementation in a different page. Finally a number of new opcodes are implemented by setting up a finite state machine that sequences the execution of multiple code fragments in the vCPU time slices, then eventually returns to the regular vCPU execution process. This is explained in [this post](https://forum.gigatron.io/viewtopic.php?p=3714#p3714) and additional details can be found in the next section of this document.

* Direct implementation in page 3 offers the best speed and therefore is used for the most frequently used vCPU opcodes such as [`LDW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2199-L2211) or [`ADDW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2486-L2511).
* Jumping to an out-of-page implementation from page 3 typically costs three to four additional cycles but only requires two or three bytes in page 3. Therefore all ROM versions contain many such instructions as explained in this [very old comment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv1.asm.py#L1512-L1517).
* Direct implementation in page 23 offers the best speed for prefix `0x35` opcodes. DEV7ROM uses this strategy for the conditional branch instructions and for the [`DOKEI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7852-L7869) opcode. Processing the prefix `0x35` and jumping around costs four to five cycles for regular instructions. Branches can hide some of this overhead because it overlaps their normal operation.
* A few page 23 opcodes simply jump to code located in other pages. This is difficult to use because all this jumping takes from the 30 cycles budget and does not leave much time for actual work. Such instructions either stall for more cycles or setup a finite state machine to do their work.
* Most page 23 opcodes branch to helper code that collects their arguments and sets up a finite state machine. This will be explained in the next section with more details.

All this means that page 3 is a very busy place. The DEV7ROM changes not only includes moving the implementation of some opcodes outside page 3, but also bringing back the implementation of certain opcodes that used to live in page 3 for ROMv4 and were moved away for ROMv5a. This is achieved by finding creative ways to share code, while avoiding the locations that must be maintained to ensure backward compatibility.  In DEV7ROM, there are just two spots available for new opcodes in page 3, [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2416-L2148) and [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2518-L2520). In contrast, there is still plenty of space in page 23.



#### Traditional vCPU opcodes

The following table lists the traditional vCPU opcodes and points to their implementation.
These official opcodes are explained in the [vCPU summary](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU-summary.txt).

| Opcode name | Encoding   | Implementation
|-------------|------------|-------
| [`LDWI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2167-L2174) | `11 LL HH` | Shorter implementation in page 3, [sharing code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2208-L2211) with `LDW`.
| [`LD`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2183-L2181) | `1a DD` | Returned to page 3, also [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2572-L2578).
| [`CMPHS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2194-L2191) | `1f DD` | Faster implementation in [page 11](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4130-L4143).
| [`LDW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2200-L2211) | `21 DD` | Implemented in page 3, modified to share code with `LDWI`.
| [`STW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2214-L2222) | `2b DD` | Shorter implementation in page 3.
| [`BEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7778-L7793) | `35 3f DD` | Faster reimplementation in page 23, sharing code with other conditional branch opcodes. 
| [`BGT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7806-L7812) | `35 4d DD` | same.
| [`BLT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7814-L7820) | `35 50 DD` | same.
| [`BGE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7814-L7828) | `35 53 DD` | same.
| [`BLE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7830-L7846) | `35 56 DD` | same.
| [`BNE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7871-L7886) | `35 72 DD` | same.
| [`LDI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2340-L2347) | `59 DD` | Unchanged in page 3.
| [`ST`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2349-L2355) | `5e DD` | Unchanged in page 3.
| [`POP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2349-L2362) | `63` | Reimplemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10419-L10457) for 16 bits `vSP`.
| [`PUSH`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2409-L2414) | `75` | Reimplemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10379-L10417) for 16 bits `vSP`.
| [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2434-L2438) | `7f DD` | Reimplemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10654-L10664).
| [`ANDI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2440-L2443) | `82 DD` | Returned to page 3, [sharing code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2576-L2578) with `LD`.
| [`CALLI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2446-L2450) | `85 LL HH` | Implemented in [page 11](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4067-L4080).
| [`ORI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2452-L2456) | `88 DD` | Same implementation in page 3.
| [`XORI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2459-L2464) | `8c DD` | Same implementation in page 3.
| [`BRA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2466-L2470) | `90 DD` | Same implementation in page 3.
| [`INC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2472-L2477) | `93 DD` | Returned to [page 3](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2188-L2191) and [sharing code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2576-L2578) with `LD`.
| [`CMPHU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2479-L2483) | `97 DD` | Faster implementation in [page 11](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4145-L4158).
| [`ADDW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2485-L2510) | `99 DD` | Same implementation in page 3.
| [`PEEK`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2513-L2516) | `ad` | Similar implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2839-L2852). 2-bytes jump instead of 3-bytes jump.
| [`SYS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2546-L2550) | `b4 DD` | Mostly implemented in page 3. Self-restart [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2587-L2589) and [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2928-L2935).
| [`DEF`	](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2598-L2602) | `cd DD` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2753-L2764).
| [`CALL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2604-L2609) | `cf DD` | Moved to [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2937-L2954).
| [`ALLOC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2643-L2646) | `df DD` | Reimplemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10333-L10364) for 16 bits `vSP`.
| [`ADDI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2663-L2667) | `e3 DD` | Faster implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2781-L2801).
| [`SUBI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2669-L2673) | `e6 DD` | Faster implementation in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10864-L10886).
| [`LSLW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2675-L2680) | `e9` | Faster implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2803-L2823).
| [`STLW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2682-L2686) | `ec DD` | Reimplemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10459-L10500) for 16 bits `vSP`.
| [`LDLW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2691-L2694) | `ee DD` | Reimplemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10503-L10550) for 16 bits `vSP`.
| [`POKE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2697-L2700) | `f0 DD` | Changed to provide overlapped instruction with `LDLW`. Implemented in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2825-L2837).
| [`DOKE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2702-L2706) | `f3 DD` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2854-L2868).
| [`DEEK`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2708-L2712) | `f6` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2870-L2883).
| [`ANDW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2714-2717) | `f8 DD` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2885-L2898).
| [`ORW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2720-2724) | `fa DD` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2900-L2914).
| [`XORW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2726-2730) | `fc DD` | Same implementation in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2916-L2926).
| [`RET`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2733-L2751) | `ff` | Same implementation straddling pages 3 and 4.

#### New vCPU opcodes dispatched in page 3

The following table lists the new opcodes implemented in page 3 and points to their implementation. These opcodes are explained in the [vCPU7 documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md).

| Opcode name | Encoding   | Implementation
|-------------|------------|-------
| [`NEGV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2176-L2180) | `18 DD` | Implemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10611-L10628).
| [`ADDHI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2224-L2229) | `33 DD` | Implemented in page 3, [sharing code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2344-L2347) with `LDI`.
| [`POKEA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2239-2245) | `39 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8376-L8385).
| [`DOKEA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2247-L2253) | `3b DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8387-L8402).
| [`DEEKA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2255-L2262) | `3d DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8404-L8421).
| [`JEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2264-L2270) | `3f LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8646-L8661) sharing code with the other `JCC` opcodes.
| [`DEEKV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2272-L2278) | `41 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8460-L8475).
| [`DOKEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2280-L2284) | `44 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8432-L8441).
| [`POKEQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2286-L2290) | `46 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8423-L8430).
| [`MOVQB`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2292-L2296) | `48 DD II` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10832-L10845)
| [`MOVQW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2299-L2303) | `4a DD II` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10847-L10862)
| [`JGT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2305-L2312) | `4d LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8663-L8674) sharing code with the other `JCC` opcodes.
| [`JLT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2314-L2321) | `50 LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8692-L8702) sharing code with the other `JCC` opcodes.
| [`JGE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2323-L2330) | `53 LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8676-L8690) sharing code with the other `JCC` opcodes.
| [`JLE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2332-L2338) | `56 LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8704-L8710) sharing code with the other `JCC` opcodes.
| [`ADDV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2364-L2368) | `66 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8574-L8600).
| [`SUBV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2370-L2374) | `68 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8602-L8625).
| [`LDXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2376-L2380) | `6a DD LL HH` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10888-L10905) then [fsm page 28](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9628-L9665). 
| [`STXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2382-L2386) | `6c DD LL HH` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10907-L10912) sharing code with `LDXW`, then [fsm page 28](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9667-L9698).  
| [`LDSB`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2388-L2392) | `6e DD` | Implemented in [page 4](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2766-L2778)
| [`INCV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2394-L2398) | `70 DD` | Implemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10593-L10609).
| [`JNE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2400-L2407) | `72 LL HH` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8627-L8644) sharing code with the other `JCC` opcodes.
| [`DBNE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2420-L2425) | `7a DD BB` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10914-L10935).
| [`MULQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2427-L2432) | `7d KK` | Implemented in [fsm page 29](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9911-L10022).
| [`MOVIW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2522-L2528) | `b1 DD HH LL` |  Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8555-L8572).
| [`MOVW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2560-L2569) | `bb DD SS` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10805-L10830), self-restarting.
| [`ADDSV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2580-L2584) | `c6 DD II` | Implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10938-L10963), then possibly [fsm page 33](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10996-L11027). 
[`CMPWS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2611-L2616) | `d3 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8518-L8527) jumping into `CMPWU` implementation.
| [`CMPWU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2618-L2623) | `d6 DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8477-L8516).
| [`CMPIS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2625-L2629) | `d9 II` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8543-L8553) jumping into `CMPWU` implementation.
| [`CMPIU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2631-L2635) | `db II` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8521-L8531) jumping into `CMPWU` implementation.
| [`PEEKV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2637-L2641) | `dd DD` | Implemented in [page 25](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8444-8458).
| [`PEEKA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2648-L2654) | `e1 DD` | Implemented in [page 11](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4165-L4175).


#### New vCPU opcodes dispatched in page 23

Page 23 dispatches a substantial number of the new opcodes described in the [vCPU7 documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md).

Most of the opcodes dispatched in page 23 are implemented with finite state machines. The following table lists the few new opcodes which are not. This is in addition to the traditional conditional branch opcodes described earlier.

| Opcode name | Encoding | Implementation
|-------------|----------|--------------
| [`LDLAC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7671-L7677) | `35 1e` | Implemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10571-L10590).
| [`STLAC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7679-L7685) | `35 20` | Implemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10552-L10569).
| [`DOKEI`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7852-L7869) | `35 63 HH LL` | Implemented in page 23.
| [`RESET`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7893-L7898) | `35 7d` | Implemented in [page 31](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10632-L10639).

The remaining new opcodes in page 23 are tightly connected to finite state machines and best listed by their fsm page.

| FSM page | Opcode names
|----------|--------------
| [fsm 20](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6572) | [`MULW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7774), [`RDIVU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7767), [`RDIVS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7759), also used by [`SYS_Multiply_s16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L850-L872) and [`SYS_Divide_u16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L874-L900), relayed [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6534-L6560).
| [fsm 21](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6901) | Implements [`SYS_Loader`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L942-L979) and micro-ops.
| [fsm 22](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7248) | Implements [`SYS_Exec`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L918-L940) relayed [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10681-L10693).
| [fsm 24](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8071) | [`COPY`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7978), [`COPYN`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7991), [`MOVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8022), [`MOVF`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8030), [`COPYS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7567), [`EXBA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7998).
| [fsm 26](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8721) | [`SUBL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7575), [`ANDL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7581), [`ORL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7589), [`XORL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7596), [`LDFAC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7704), [`LDFARG`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7714).
| [fsm 27](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9043) | [`ADDL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7559), [`NEGX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7610), [`NEGVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7603), [`NOTVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8005), [`LSLVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7618), [`INCVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7690), [`LEEKA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7739), [`LOKEA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7746).
| [fsm 28](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9381) | [`LSRXA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7650), [`RORX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7659), plus second part of [`STXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2384) and [`LDXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2378) dispatched from page 3.
| [fsm 29](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9709) | [`MACX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7667), plus implementation of [`MULQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2430) dispatched from page 3.
| [fsm 30](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10032) | [`CMPLS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7634), [`CMPLU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7642), [`LSLXA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7626), [`STFAC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7697).
| [fsm 33](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10976) | [`VSAVE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7720), [`VRESTORE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7727), plus enhanced vIRQ and carry part of [`ADDSV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2582) dispatched from page 3.
| [fsm 34](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11201) | [`FILL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7801), plus implementation of [`SYS_DoubleDabble`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1046-L1065), relayed [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10752-L10769).
| [fsm 35](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11482) | [`BLIT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7796).
 
Good opportunity to discuss these finite state machines.

## 5. Finite state machines

See the [forum post](https://forum.gigatron.io/viewtopic.php?p=3714#p3714) for general explanation of DEV7ROM's finite state machines.

### 5.1. FSM page 20: multiplication and division

Let start with a closer look at the multiplication code. 

The DEV7ROM [`SYS_Multiply_s16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L850-L872) is compatible with the ROMv6 [native multiplication]([`SYS_Multiply_s16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L850-L872). On the surface, it only differs because it does not require the user to set word `sysArgs[6:7]` to one. However its implementation is completely different.

* The SYS call [entry point](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L850-L872) merely calls [`sys_Multiply_s16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6534-L6545) which lives in page 19, right before the finite state machine.
* This code [sets variable `fsmState`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6536-L6537) to the address of the first fragment of the multiplication routine in the fsm page. In fact [`fsmState`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L382) is just another name for `sysArgs[7]`. Then it [initializes the multiplicator mask byte](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6538-L6539).
* The rest of the code fires the state machine. It [sets variable `vcpuSelect`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6540-L6541) to the page that contains the finite state entry point, then [jumps into the dispatcher](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6543-L6545) of the multiplication machine.

The `vCpuSelect` variable was introduced in ROMv5a to provide the means to switch virtual cpus, for instance vCPU vs v6502. Here it is used to inform the gigatron main loop that we are no longer dispatching vCPU opcodes, but code fragments defined by the finite state machine.

* Soon after, the dispatcher branches to the [first fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6596-L6619) of the multiplication code. Its first instructions [set the address of the next fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6597-L6598). Then the code ands the mask with the low multiplicator byte. If this is zero, it returns to the dispatcher (10 cycles), otherwise it adds the multiplicand to the product and returns to the dispatcher (24 cycles).
* Soon after, the dispatcher executes the [second fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6621-L6648). This code [left shifts the multiplicand](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6622-L6629) then [shifts the mask](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6630-L6633) and continues to the first fragment until the mask is zero.
* When the mask is zero, we're finished with the low multiplicator byte. Therefore the code [resets the mask and sets the next fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6640-L6648) to the code that deals with the high multiplicator byte. Note the optimization that sets the mask to zero if the high multiplicator byte is zero.
* The [final fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6650-L6679) is simpler because there is no need to perform 16 bits additions. It ands the mask and the high multiplicator byte, if non zero, adds the multiplicand byte to the product (but we know that the low multiplicand byte is zero after eight or more shifts), and shifts both multiplicand and mask. It then jumps into the dispatcher which will invoke the same code again (because `fsmState` is unchanged) until the mask becomes zero. When this happens, the fragment [copies the result into `vAC`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6670-L6674) and [exits the finite state machine](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6675-L6679) by resetting `vCpuSelect` and jumping into the vCPU dispatcher in page 3.

All this is quite efficient because the finite state machine dispatcher overhead can be as low as three cycles, and because the code fragment start at cycle 3 out of the allowed 30, leaving time to do more things than possible in a typical vCPU opcode.

The same multiplication machine is used by the [`MULW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7774) opcode. Its [dispatching code in page 23](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7775-L7776) illustrates a pattern shared by many fsm based opcodes. It sets the address of the first fragment in the delay slot of a branch instruction towards a stub that fires the finite state machine. There are multiple stubs dealing with various finite state machines and different numbers of opcode arguments. 
* The [simplest stubs](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8034-L8041) target opcodes without arguments such as [`ADDL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7559) and many other opcodes.
* The [most complex stub](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7954-L7969) accepts to arguments that are stored in `sysArgs[5]` and `sysArgs[6]` before firing the state machine. This is only used by three opcodes, [`MOVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8022), [`MOVF`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8030), and [`COPYS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7567), implemented in fsm page 24.
* Instruction [`MULW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7774) uses a stub that collects a single argument into `sysArgs+6`. One argument stubs are [implemented](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7924-L7927) with an [indirection](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7911-L7921) in order to share code. This was possible because there was one cycle left to obtain the required even number of cycles.

All this machine provides the means to implement SYS calls and vCPU opcodes that perform complicated tasks by splitting them into little pieces that are scheduled individually. The [division code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6682-L6812) follows a similar pattern. It can be entered as a SYS call [`SYS_Divide_u16`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L874-L900) that is compatible with ROMv6 but performs unsigned division on all 16 bits instead of just 15. It can also be entered with the vCPU opcodes [`RDIVU`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7767) for unsigned division or [`RDIVS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7759) which involve additional logic for signed division. All three return the quotient in both `vAC` and `sysArgs[0:1]`, and the remainder in `sysArgs[4:5]`.

### 5.2. FSM pages 26, 27, 28, 29, 30: mostly long integer support

These pages mostly implement a collection of prefix `0x35` vCPU opcodes that either operate on long integers or help working with floating point numbers. Many of these opcodes are two bytes long (including the prefix byte) because they implicitly operate on either the long accumulator `vLAC`, the extended long accumulator `vLAX`, and possibly the floating point exponent `vFAE` and sign `vFAS`.  Register `vAC` is often used to hold another argument such as a pointer to another long integer. See the table above for the list of opcodes implemented by each finite state machine, and consult the [vCPU7 documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md) for the details.

There are a couple exceptions:

* FSM page 27 contains several opcodes with a single byte argument that indicates the position of a long integer in page zero: [`NEGVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7603), [`NOTVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8005), [`LSLVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7618), [`INCVL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7690), [`LEEKA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7739), and [`LOKEA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7746).
  
* FSM page 28 implements the right shift instructions [`LSRXA`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7650) and [`RORX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7659). It also contains the second part of the implementation of the opcodes [`STXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2384) and [`LDXW`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2378). These opcodes are in fact dispatched from page 3 and jump into [code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10888-L10912) that collects their arguments and fires the state machine to continue their execution with a [code fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9628-L9698) located in page 28.

* FSM page 29 implements the [`MACX`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7667) opcode, a prefix opcode dispatched from page 23, as well as the [`MULQ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2430) opcode, which is dispatched from page 3 and [fires a finite state machine](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9729-L9743) to do the work. 

### 5.3. FSM page 24: copy opcodes

FSM page 24 contains the copy machine which can seamlessly copy memory fragments that straddle page boundaries. The [`COPY`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7978), [`COPYN`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7991), and [`COPYS`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7567) opcodes essentially are three frontends for this copy machine.

The copy machine  tries hard to copy memory in four byte pieces. For this to happen, there must be more than four bytes left to copy, and neither the source pointer nor the destination pointer should straddle a page boundary when copying these four bytes. If any of these conditions is violated, one has to process the copy byte-per-byte until all three conditions are met.

* Fragment [`copy#3a`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8117) first checks whether there are less than four bytes left to copy and jumps into the code of fragment `copy#3b` if this is the case. Then it tests whether the source pointer approaches a page boundary and, if this is the case, sets `fsmState` to fragment `copy#3b` and returns to the dispatcher. Finally is reads four source bytes into `sysArgs[2:5]` and schedules fragment `copy#3d`.
* Fragment [`copy#3b`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8153-L8186) copies a single byte and increments both the source pointer `vT3` and the destination pointer `vT2`. If it encounters a page boundary, it schedules fragment `copy#3d`. Otherwise it returns to the dispatcher. The next fragment will then be either `copy#3a` (when copying the final four bytes) or `copy#3b` (otherwise).
* Fragment [`copy#3c`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8188-L8214) fixes the source and destination pointers to deal with page crossings and schedules `copy#3a`.
* Fragment [`copy#3d`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L8216-L8261) checks whether the destination pointer approaches a page boundary. If this is not the case, it writes the four bytes saved in `sysArgs[2:5]` and schedules `copy#3a` to keep copying. Otherwise it only writes the byte saved in `sysArgs[2]`, corrects the source and destination pointers, and schedules `copy#3b` to copy byte-per-byte until reaching a page boundary.

In addition, fragments `copy#3[bcd]` also update the count of remaining bytes to copy and exit the state machine when done. It takes a little bit of effort to convince oneself that this complicated control flow will efficiently do the right thing for all combinations of page crossing and all numbers of remaining bytes to copy. 

### 5.4. FSM pages 34 and 35: fill and blit

Although opcode [`FILL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7801) is often used to fill a rectangular area in the frame buffer, this is a strict superset of the functionality offered by the traditional SYS call [`SYS_SetMemory`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3634-L3651). In ROMv6, `SYS_SetMemory` is a [self-restarting SYS call](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L3239-L3245) that can set up to 24 bytes whenever the video loop gives one scanline to the vCPU. DEV7ROM saves precious cycles by [looping immediately if enough cycles are available](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3917-L3929) for a new iteration. This trick allows for setting up to 32 bytes per scanline, a 33% speed gain.

Opcode `FILL`, implemented in [fsm page 34](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11297), sets up 60 bytes per scanline, more than twice what `SYS_SetMemory` can achieve in ROMv6. Although the low dispatching overhead of finite state machines play a role in this performance, two additional tricks make this possible:

* The code fragment that initiates the copy of each row makes sure that the number of pixels to copy is even. Otherwise it [copies one pixel itself](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11328-L11330) and even dispatches a special code fragment for single pixel wide rectangles, that is, [vertical lines](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11423). 
* The code fragment that copies each row can set up to 12 bytes in 28 cycles. But it starts with the last 12 bytes of the row and works its way backwards until only 2, 4, 6, 8, or 10 bytes remain. It handles these cases by [jumping into specialized branches](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11349-L11355) that eventually jump into the right location of the 12 byte burst and with the right timing. 

The [`BLIT`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7796) code in [fsm page 35](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11501) follow a similar pattern but must use different fragments for [reading](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11586-L11602) and [writing](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11638-L11654). It also includes [logic to decide in which direction to process the rows and columns](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11525-L11577) to ensure that [overlapping rectangles are copied without overwriting themselves](https://forum.gigatron.io/viewtopic.php?p=4442#p4442). 

Besides implementing the `FILL` opcode, [fsm page 34](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11220) also implements the new [`SYS_DoubleDabble`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1046-L1065) sys call which provides a general way to quickly convert binary integers into an arbitrary base. Simply initialize the buffer to zero and call the SYS call for every bit in the integer, starting with the most significant one. For instance, the GLCC compiler library converts numbers to ASCII by either [using this SYS Call](https://github.com/lb3361/gigatron-lcc/blob/master/gigatron/libc/itoa.s#L85-L93) or [emulating it with vCPU instructions](https://github.com/lb3361/gigatron-lcc/blob/master/gigatron/libc/itoa.s#L55-L75).


### 5.5. FSM page 21 : SYS_Loader and fsm microprogramming

The DEV7ROM loader is almost entirely implemented by SYS call [`SYS_Loader`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L942-L979) which only uses the `sysArgs` array as temporary variables and therefore can load code or data anywhere in memory, except for the essential page zero variables in range `0x00-0x2f`.  Like the ROMv6 loader, it can display a feedback bar but will switch it off if it detects that data is loaded in the memory area that is used to display the bar. As a result the [`Loader.gcl`](https://github.com/lb3361/gigatron-rom/blob/doc/Apps/Loader/Loader.gcl) is reduced to [displaying a friendly message](https://github.com/lb3361/gigatron-rom/blob/doc/Apps/Loader/Loader.gcl#L33-L38) and [invoking the sys call](https://github.com/lb3361/gigatron-rom/blob/doc/Apps/Loader/Loader.gcl#L44-L46).

The loader sys call is implemented in [FSM page 21](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6896) using a micro-programming technique. In essence, the finite machine state `fsmState` is now interpreted as a program counter for a little [micro-program](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7074-L7108) that implements the loader protocol.  The `SYS_Loader` [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7110-L7124), which is called with `sysArgs0` in the accumulator, simply normalizes the arguments and fires the finite state machine with `fsmState` equal to [`sl:loader`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7075).

The implementation starts with python function [`fsmLab`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6917-L6919), which is used to construct labels that do not conflict with similar labels in other finite state machines.  Next, function [`fsmAsm`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6921-L6924) is used to emit a micro-program opcode (micro-op). Each micro-op is composed of a branch to the micro-op implementation with a `ld` instruction in its delay slot to pass an argument. As a convention, micro-ops without arguments pass the address of the following micro-op, making it easy to set `fsmState`. In contrast, micro-ops with arguments must calculate the next value of `fsmState`.

Best is to look at an example. The [`ST`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6926-L6930) micro-op. Its [actual implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7131-L7144) is designed to be callable from other finite state machines. As promised, it [first stores `vACL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7132-L7134) to the location indicated by the argument of the `ST` micro-op now found in `AC`.  Then it [increments](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7136-L7139) the micro-program counter, and [returns to the dispatcher](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7141-L7144) of the calling finite state machine.

Several micro-ops defined in fsm page 21 perform [simple 8-bit operations](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6926-L6965) using `vACL` as an accumulator. The remaining one are more specific to the operation of the loader and implicitly use the following variables:

| Variable | Used by | Description
|----------|---------|------------
| `sysArgs[1]` | `SLECHO`, `SLCHK` | feedback display page
| `sysArgs[0]` | `SLECHO`, `SLCHK` | feedback display column (0 if disabled)
| `sysArgs[2:3]` | `ST+`, `CHANMASK` | frame address
| `sysArgs[4]` | `ST+`, `CHANMASK`, `SLCHK` | frame length
| `sysArgs[6]` | `SRIN` | videoY value for next serial input
| `VLR` | `VRETNZ` | execution address

* Micro-op [`SRIN`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6990-L7025) reads the next byte from the serial input and stores it into `vACL`. The loader protocol tells at [which times](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L967-L975) bytes should be read as a list of values for the `videoY`variable: 207, 219, 235, 251, 2, 6, etc. Micro-op `SRIN` loops until `videoY` reaches the value specified in `sysArg6`, computes the next value using a tricky code, stores in into `sysArg[6]` for next time, and finally reads an input byte into `vACL`. The micro-program sets `sysArg[6]` to 207 at the beginning of each frame and then use `SRIN` to read the [frame length](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7079-L7087), the [frame address](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7095-L7099) and finally the frame data.

* Micro-op [`ST+`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6974-L6980), implemented [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7221-L7237), stores `vACL` at the address `sysArg[2:3]`, increments the address low byte for next time, decrements the length `sysArg[4]` and returns it into `vACL` to be tested. This is used in the [loop that reads and stores the frame data](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7103-L7106).

* Micro-op [`CHANMASK`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6982-L6988), implemented [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7200-L7219), disables the sound channels 2,3, and 4 if the loader tries to load data in their counter bytes. Micro-op [`SLCHECK`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7055-L7072) checks the frame information, returning a non zero value if invalid. It also disables the feedback display if the loader tries to load data where the feedback pixels are. Both are called to [validate the frame information](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7100-L7102) before reading the frame data.

* Micro-op [`SLECHO`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7027-L7053) displays a feedback pixel in the color specified by `vACL`, [grey for invalid frames](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7076-L7078) and [green for completed frames](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7107-L7108).

* Finally, the micro-program [reads the execution address](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7088-L7094) into `vLR` and calls micro-op [`VRETNZ`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6967-L6972), implemented [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7182-L7198), to exit the finite state machine and point the vCPU to the execution address. However, if `vLR` is zero, `VRETNZ` merely returns into an endless loop.


### 5.6. FSM page 22 : SYS_Exec and GT1 compression

The gigatron loads program stored in ROM using [`SYS_Exec`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L918-L940). 
In all official roms up to ROMv6, the `SYS_Exec` code works by creating and executing a little vCPU program slighlty below the stack pointer. This is convenient because the easiest way to read ROM data is the vCPU `LUP` opcode. 

DEV7ROM instead implements `SYS_Exec` with a finite state machine microprogram that resembles that of `SYS_Loader` but is considerably more involved because it can load both GT1 data or compressed GT1 data. The GT1 compression story can be found in the [forum](https://forum.gigatron.io/viewtopic.php?p=4139#p4139) and the format is described in the [documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/GT1-compression.txt) and demonstrated by function `decompress` in the [source code](https://github.com/lb3361/gigatron-rom/blob/doc/Utils/gt1z/gt1z.cpp#L606-L697) of the `gt1z` utility program.  

Like `SYS_Loader`, `SYS_Exec` only uses zero page variables located in the essential region `0x00-0x2f`. This means that it can load code or data anywhere else in the Gigatron memory. Pretty much everything available is used including `vACH` and `sysFn`. The [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10678-L10693) is located in page 32. It initializes `sysFn` to `0x0001`, overwriting the address of the sys call, sets `fsmState` to the micro-program entry point [`se:exec`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7435), and fires the finite state machine. Before returning to the vCPU, the micro-program resets `sysFn` to its initial value, which is the value a vCPU program would have found when just loaded.

| Variable | Used by | Description
|----------|---------|------------
| `sysArgs[0:1]` | `LUP` | rom address of next data byte
| `sysArgs[2:3]` | `ST+`, `CHANMASK`, `LDMATCH`, `OFFSET` | segment address
| `sysArgs[4]` | `ST+`, `CHANMASK`, `SLCHK` | segment length
| `sysArgs[5]` | u-prog | initial low segment address byte
| `sysArgs[6]` | `BL` | link register for subroutine
| `sysFn` | `LDMATCH`, `OFFSET` | offset for matched copies, initially 1.
| `vACH` | u-prog | saved token describing the current gt1z record.
| `vACL` | all | accumulator for the u-ops.
| `VLR` | `VRETNZ` | execution address

* Many of the [micro-ops defined for fsm page 22](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7273) are copies of the similarly named micro-ops defined in page 21 for the loader and often point to their implementation in page 21. Besides general operations on `vACL`, this includes the [`VRETNZ`, `CHANMASK`, and `ST+` micro-ops](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7337-L7358) discussed in the loader section above.

* Micro-op [`LSR4`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7299-L7304), implemented [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7151-L7159) and [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3510-L3515), rights shifts `vACL` by four bits in order to extract its high nibble.
  
* Micro-op [`BL`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7328-L7335) invokes micro-program subroutines, saving the return address in byte `sysArgs[6]`. For instance, the exec microprogram contains a [subroutine](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7398-L7405) to store `sysArg[4]` bytes read from rom address `sysArgs[0:1]` at ram address `sysArgs[2:3]`

* Micro-op [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7360-L7382) plays the most important role. It reads the rom byte located at address `sysArgs[0:1]` into `vACL` and also increments `sysArgs[0:1]` to point to the next rom byte, skipping the trampoline located in the end of every page containing lup data. Unlike the vCPU opcode `LUP`, the micro-op `LUP` does not set `vACH` to zero, making `vACH` usable to store the compressed GT1 record token. Implementing this was quite complex because it *forces a cascade of changes described later in this section*.

* Finally, micro-op [`LDMATCH`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7384-L7396) reads a byte in ram located at an address computed by subtracting (without carries) the offset `sysFn` from the current writing address `sysArgs[2:3]`. This is used to implement matched copies in compressed GT1 data.

Armed with these micro-ops, the micro-program first [inspects the first rom bytes](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7435-L7444). If these bytes are not `0x00` and `0xff`, it simply jumps into [micro-code that loads uncompressed GT1 segments](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7407-L7417). After processing the last segment, this code falls through into [final micro-code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7419-L7431) which restores `sysFn` and uses `VRETNZ` to exit the finite state machine pointing the vCPU to either the address provided in `vLR` or to the execution address read from rom. 

Otherwise the entry micro-code jumps into the compressed GT1 loading routine, obtaining [the first segment address](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7450-L7454), and looping over compressed GT1 records. 
Each record starts with a [token byte](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7455-L7460) that encodes both the [number of *literal* bytes](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7461-L7465) to [copy from rom](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7466-L7467), and the [number of *matched* bytes](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7468-L7473) to [copy from ram](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7489-L7493) after [extacting the mactching offset](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7474-L7488). A [number of matched bytes equal to zero](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7471) indicates that it is time to start a new segment.

#### Breaking out of micro-programming

The [new segment code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7498-L7511) is not implemented with micro-ops but as a regular fragment of fsm code. Although it could have been implemented with the following micro-code, the direct implementation ends up being more compact. 
```python
label('se:loadGt1z:seg')
fsmAsm('LD', [vAC+1])
fsmAsm('AND', 0x80)                   # check the high token bit
fsmAsm('BZ', 'se:loadGt1z:longseg')   # if zero we must get two segment address bytes
fsmAsm('LD', [sysArgs+5])             # otherwise, we add 256 to the old segment address
fsmAsm('ST', sysArgs+2)               
fsmAsm('LD', [sysArgs+3])
fsmAsm('ADD', 1)
fsmAsm('ST', sysArgs+3)
fsmAsm('B', 'se:loadGt1z:token')
```
The same holds that deals with [short offsets](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7513-L7538). Writing this with micro-ops would have required a space in page 22 that was simply not available. Whatever works works!

#### LUP timing changes

Implementing the [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7360-L7382) micro-op forced subtle timing changes on the [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2434-L2438) vCPU opcode, first to avoid writing `vACH` when returning from the LUP trampolines, and second to create enough time to increment the LUP pointer `sysArgs[0:1]`.

Whereas the ROMv6 [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L1793-L1797) vCPU opcode is implemented in page 3, the DEV7ROM [`LUP`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2434-L2438) is implemented in [page 32](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10654-L10664) and clears `vACH` before jumping into the trampoline, four cycles behind the ROMv6 version. After reading the required byte, the trampoline jumps back to the [return code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10670-L10675) which has been modified to return to the current dispatcher, be it the vCPU dispatcher (for the `LUP` vCPU opcode), or a finite state machine (for the `LUP` micro-op). 

The code that [writes the LUP trampolines](https://github.com/lb3361/gigatron-rom/blob/doc/Core/asm.py#L215-L223) hardcodes the name `lupReturn#19` and cannot be changed to `lupReturn#23` because it belongs to `asm.py` which is imported by all roms. Changing it would break all other roms. Therefore the DEV7ROM lup return code is also called [`lupReturn#19`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10669-L10670) even though it runs 23 cycles into the execution slice. 

But this is not all that is needed. The Gigatron also uses the `LUP` opcode to [return from virtual interrupts](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/Interrupts.txt). In DEV7ROM, this takes us into the [vRTI entry point](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3126-L3131) four cycles behind ROMv6. As a result all the [vRTI code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3097-L3123) has been rewritten to account for the new timings. We lucked out here because (a) the timings would not have worked with `maxTicks=14` and (b) space for the new code appeared because the implementation of opcode `INC` has been returned to page 3.


### 5.7. FSM page 33 : enhanced vIRQ

FSM page 33 is mostly devoted to implementing the [enhanced virtual interrupts (vIRQ)](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7900-L7909) and the associated vCPU opcodes [`VSAVE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7718-L7722) and [`VRESTORE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7724-L7729). 

Because there was a little bit of space left, this page also contains the [code fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10996-L11027) that sometimes runs to deal with a possible carry for the [`ADDSV`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L2580-L2584) opcode (see [the main implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L10937-L10963)). This is independent of the vIRQ system and will not be discussed further in this section.

DEV7ROM handles vIRQs differently depending on the contents of variable [`vIrqCtx`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L447). When this variable is zero (the default), vIRQs work exactly as in ROMv6. Otherwise the enhanced vIRQ system saves the full vCPU context at offsets `0xe0-0xff` in the page indicated by `vIrqCtx`. Opcode [`VSAVE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7718-L7722) can be used to manually save a context, and opcode [`VRESTORE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7724-L7729) to restore a context and resume execution where the context was saved, restarting the execution of vCPU opcodes, of v6502 instructions, or of finite state machine fragments alike. Full details can be found in the [documentation](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/vCPU7.md#context-and-interrupts). See also the experimental [library](https://github.com/lb3361/gigatron-lcc/tree/master/stuff/threads) that implements [preemptive multitasking](https://forum.gigatron.io/viewtopic.php?t=463) for the C compiler.

#### Handling virtual interrupts

As in ROMv5a and ROMv6, vIRQs are triggered by [code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1337-L1349) that runs during the first vertical blanking line and tests whether the freshly incremented `frameCount` wraps to zero. 
Because of unrelated optimization, this code runs three cycles ahead of the [equivalent ROMv6 code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L1185-L1195).

As in earlier roms, when `frameCount` is zero, execution continues with [page 18 code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L5976) that performs further tests before possibly dispatching the interrupt. Regardless of the outcome, this ends by running the vCPU dispatcher to process vCPU opcodes until the end of the available time slice. The [ROMv6 code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/ROMv6.asm.py#L5219-L5248) does this with two invocations of the `runVcpu` macro, the first one to deal with the case where no vIRQ handler is specified, the second one to dispatch the vIRQ. We would need at least two more, one to dispatch a enhanced vIRQ, and one to deal with masked interrupts. The problem is that we do not have space in page 18 to expand the `runVcpu` code four times.

In order to work around this constraint, DEV7ROM provides a separate python function [`runVcpu_ticks`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L484-L494) to compute the execution window timings. This function is then used by the [`runVcpu`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L496-L530) macro which generates the code that starts the dispatcher. 

Instead of invoking `runVcpu`, the DEV7ROM irq code invokes `runVcpu_ticks` and branches into a [shared code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L5967-L5973) that starts the dispatcher. This relies on the common value of `vReturn` which determines where to jump when the execution window ends, and which was set [just before jumping into page 18](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1345-L1346).  Using this approach, the virq code first [bails out into the dispatcher when no vIRQ handler is provided](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L5976-L5981). The vIRQ code then checks `vIrqCtx` and [performs an old style interrupt](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L5983-L6004) if zero. Otherwise we have an enhanced vIRQ which could be [masked](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6006-L6014) or [executed](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L6016-L6019) by branching to [page 32 code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11058-L11086) that uses the rest of the execution window to save the vCPU context, points the program counter to the vIRQ handler, and returns to the video loop.

#### VSAVE and VRESTORE

Most of the context saving is performed in a [piece of code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11064-L11075) that uses a python function [vSave](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11043-L11047) for brevity. 
This same piece of code is also used, with different timings, by the [`VSAVE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7718-L7722) opcode. The `VSAVE` opcode [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11092-L11103) first saves `fsmState` and `vCpuSelect`, then is free to use these variables to schedule a [finite state fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11105-L11118) that self-restarts until there is sufficient time to save everything else.

The [`VRESTORE`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L7724-L7729) code works very much in reverse. Its [implementation](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11124-L11132) restores a couple variables, then fires the finite state machine using a [first self-restarting fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11138-L11151) that restores almost everything, and a [final fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11153-L11189) that handles the [saturating `frameCount` adjustment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11154-L11171), then [proceed](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11172-L11178), restoring the variables that would otherwise have disrupted the execution of the finite state machine, clearing the interrupt mask, and testing the remaining time to [determine](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11180-L11182) whether we can [resume execution during the current time slice](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11183-L11185) or after [yielding to the video loop](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L11186-L11189).
Note that resuming the execution must be carried out using `ENTER` because this is the only dispatcher entry point that is shared by the vCPU, v6502, and FSM dispatchers. 



## 6. Video loop and variants : dev128k7.rom, dev512k7.rom

The initial goal of DEV7ROM was to provide means to swap the memory bank of a [RAM and IO extension board](https://forum.gigatron.io/viewtopic.php?p=3694#p3694) on the fly so that the vCPU runs with the memory bank configured with [`SYS_ExpanderControl`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3677-L3708) and the video output runs with the default memory bank configuration (bank 1 in `0x8000-0xffff`). Doing this efficiently requires cascading changes in the video loop. Some of the changes are there just to make it possible to make other changes, etc.  In fact the initial vCPU work was made to make space in `0x1f2-0x1f5` to displace page zero variables and make space for new ones that contain copies of the control bits to use when the vCPU or when the video output is running.

### 6.1. Resync

One change affects all the places where one resynchronizes the timing when reaching the end of a vCPU execution window. In the main vCPU page, this code looks like this:
```
# Resync with video driver and transfer control
label('EXIT')
adda(maxTicks)                  #3
label('RESYNC')
bgt(pc()&255)                   #4 Resync
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7 To video driver
ld([channel])                   #8 with channel in AC
```
In ROMv6, the last instruction is a `ld(0)` which in fact is a no-operation. In DEV7ROM, the last instruction must be `ld([channel])`. This appears in the dispatching code of all the finite state machines (e.g. [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L9057), as well as in the equivalent code in the virtual 6502 interpreter ([here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4871) and [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L5112)). This is useful because the end of the execution window is often followed by a jump to `sound` in the tight [front porch code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1994-L2027) which manipulates the horizontal sync signal while dealing with the sound generation. Having the channel already loaded shaves one cycle that can be used to swap memory banks. 

### 6.2. Vertical blanking

The Gigatron vertical blank video code, located in page 1, is rather complex and irregular. Different code during the first vertical blank line, the middle ones, and the last one. A number of changes here aim to save code space or save cycles to give a little bit of elbow room.

First vertical blank line:
* A [faster led sequencer](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1247) shaves three cycles.
* [The vIRQ entry code is different](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1337-L1349) as discussed earlier.
* A [reorganized sound timer code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1357-L1368) shaves four cycles.

Middle vertical blank lines:
* A [reorganized video pulse code](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1410-L1425) saves some precious space.
* The code [enters vblanknormal two cycles earlier](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1428-L1443), a change made necessary as explained in the `maxTicks` discussion. This possible by [combining the code that tests when it is time to capture the serial input and the code that tests when it is time to output a sound sample.](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1445-L1466).

Last vertical blank lines:
* A additional vCPU execution window runs when the user [presses the select button](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1577-L1583).
* The [final code vertical blank code fragment](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1586-L1599) no longer jumps into the page 2 code. Instead it has been positionned at the end of page 1 so that it falls through into page 2. This new path saves space, cycles, and remove the need to increment the channel in the page 1 code.

### 6.2. Visible video lines

The Gigatron code that outputs visible scanlines is located in page 2 and is notoriously tight. 
DEV7ROM contains separate versions of this code for the regular Gigatron, the 128K Gigatron, and the 512K Gigatron

```python
if WITH_512K_BOARD:
  ... # code for the 512k gigatron
elif WITH_128K_BOARD:
  ... # code for the 128k gigatron (swapping memory banks on the fly)
else:  # NORMAL VIDEO CODE
  ... # code for the regular gigatron
```

The [code for the regular Gigatron](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1966-L2108) is the same as ROMv6 except for the additional indentation. The [code for the 128K Gigatron](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1817-L1962) is a variation of the code for the regular Gigatron. The [code for the 512K Gigatron](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1637-L1813) is markedly different but overall irrelevant to this discussion because the 512K Gigatrons is not a canonical machines.

Therefore we can just list where the code for the 128k Gigatron differs from the regular one.

* When `WITH_128K_BOARD` is defined, the rom maintains a copy of [`ctrlBits`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L449) in the zero page private variable [`ctrlCopy`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L389) and another version that points to bank 1 in variable [`ctrlVideo`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L318). This is initialized during [boot](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L719-L720) and [softreset](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L764-L765), and maintained with a special version of [`SYS_ExpanderControl`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L3677-L3699), see [here](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L4535), and with code that [refreshes these copies](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1324-L1335) during the first vertical blanking line.

* All the vertical blanking code runs with the memory bank selected for the vCPU. This is achieved during the [first vertical blanking line](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1330). Switching the video memory bank is only necessary when we output pixels.

* The [entry point](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1817-L1821) of the 128k gigatron video output loop is in `0x1fe` instead of `0x1ff`, at cycle #199 instead if #200. This is reflected in the final part of the code that implements the last vertical blanking line. The entry point code loads `ctrlVideo` and sets memory bank accordingly, that is, bank 1 because of the way `ctrlVideo` was [initialized](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L764-L765) during softreset.
  ```
  assert pc() == 0x1fe
  ld([ctrlVideo],X)               #199
  bra('sound3')                   #200,0 <New scan line start>
  align(0x100, size=0x100)
  ctrl(X)                         #1 Reset banking to page1.
  ```
Note that this code does not load variable `channel` in the accumulator. This is instead achieved in the [resynchronization code](https://github.com/lb3361/gigatron-rom/blob/doc/Docs/DEV7ROM_TOUR.md#61-resync).  The video output code is then identical to that of the regular Gigatron except for the [`nopixels`](https://github.com/lb3361/gigatron-rom/blob/doc/Core/dev.asm.py#L1956-L1962) code that invokes the vCPU dispatcher. 
```python
  label('nopixels')
  ld([ctrlCopy],X)                #38
  ctrl(X)                         #39
  runVcpu(199-40,
          'FBCD line 40-520',
          returnTo=0x1fe)         #40 Application interpreter (black scanlines)
```
This code restores the vCPU memory bank before execution vCPU opcodes, then returns to the entry point `0x1fe` at cycle #199. 
Overall this steals four cycles from the vCPU execution windows (144 cycles instead of 148). Two are lost before before invoking `runVcpu`, another is lost because one returns at cycle #199 instead of #200, and a last one arises because 199-40 is an odd number. Although saving a single cycle somewhere would gain two execution window cycles, I was unable to do it. 


## 7. Conclusion

I believe that this document gives a good description of the changes in DEV7ROM relative to ROMv6. More precisely, the changes that are not described here, for instance the precise implementation of such or such opcode, are changes that are localized to the implementation of that opcode and do not affect anything else. Instead I chose to describe the changes that are interlocked in cascading chains, which are the ones to pay attention to if one wants to import a DEV7ROM feature into another ROM, for instance.

Also this document is bound the October 2025 version of the DEV7ROM (github commit id f5d588). 



