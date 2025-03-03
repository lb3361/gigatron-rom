# vCPU7 new opcodes

The vCPU7 instruction set is a strict superset of the ROMv5a
instruction set also known as vCPU5.  The new registers and the new
opcodes are defined in the file `Core/interface-dev.json`
supplementing the standard definitions in `interface.json`.


### Registers

vCPU7 extends the stack pointer `vSP` to 16 bits and adds
a 32 bits long accumulator `vLAC`,
a 40 bits extended accumulator `vLAX` whose high 32 bits overlap `vLAC`,
two byte registers `vFAS` and `vFAE` which, together with `vLAX` form
a floating point accumulator, and
two 16 bits scratch registers `vT2` and `vT3` which are used
as destination and source registers by copy opcodes.


| Register name |    Address  | Purpose | Notes
|---------------|-------------| ------- | ----
| `vPC`         | `0x16-0x17`   | Program counter (16 bits).  | Same as vCPU5.
| `vAC`         | `0x18-0x19`   | Word accumulator (16 bits). | Same as vCPU5.
| `vLR`         | `0x1a-0x1b`   | Link register (16 bits).    | Same as vCPU5.
| `vSP`         | `0x1c-0x1d`   | Stack pointer (16 bits).    | Extended to 16 bits.
| `vLAC`        | `0x84-0x87`   | Long accumulator (32 bits)            | New
| `vLAX`        | `0x83-0x87`   | Extended accumulator (40 bits)        | New Overlaps `vLAC`
| `vFAS`        | `0x81`        | Floating point accumulator sign byte  | New
| `vFAE`        | `0x82`        | Floating point exponent               | New
| `vT2`         | `0x88-0x89`   | Destination register (16 bits)        | New
| `vT3`         | `0x8a-0x8b`   | Source register (16 bits)             | New


### Compatibility with vCPU5

vCPU7 is fully compatible with vCPU5 provided that one only uses vCPU5
instructions and than one keeps the high byte of `vSP` (known as
`vSPH`) equal to zero.  When this is the case, `vSPH` is guaranteed to
remain equal to zero. Such programs can freely use the memory
locations assigned to the new vCPU7 registers because none of the
vCPU5 opcodes are going to change them.

All vCPU5 opcodes are provided with the same encodings. The few timing
changes are reported below. Conditional branches are two cycles
faster, making up for slightly slower stack operations and indirect
call operation.

| Opcodes | Cycles
| ------- | ------
| `BEQ` `BNE`      | ! 24/24 instead of 28
| `BLT` `BGE`      | ! 24/24 instead of 28
| `BGT`            | ! 26/26 instead of 28
| `BLE`            | ! 26/24 instead of 28
| `ORW` `ANDW`     | ! 26 instead of 28
| `ADDI` `SUBI`    | ! 24 (26 with carry) instead of 28
| `LD`             | ! 18 instead of 22 (like romv4)
| `ANDI` `INC`     | ! 18 instead of 20
| `LSLW`           | ! 26-28 instead of 28
| `CMPHU` `CMPHS`  | ! 20-26 instead of 22-28
| `SUBW`           | 30 instead of 28
| `CALL`           | 30 instead of 26
| `PUSH`           | 28 instead of 26 (38 when crossing a page)
| `POP`            | 30 instead of 26 (38 when crossing a page)
| `ALLOC`          | 24 instead of 14 when `vSPH`=0, 28 or 30 otherwise
| `STLW`           | still 26 when `vSPH`=0, 36 otherwise
| `LDLW`           | still 26 when `vSPH`=0, 36/38 otherwise
| `LUP`            | 28 instead of 26


### True 16 bits stack

All stack management opcodes work exactly like their vCPU5
counterparts when the high byte of the stack pointer `vSPH` is
zero. When this is the case, they only change the low byte of the
stack pointer `vSPL`, therefore keeping `vSPH` equal to zero.

The true 16 bits stack is enabled when `vSPH` is nonzero and `vSPL` is
even.  The stack operations are then modified as follows:

* The `PUSH` and `POP` operations then can cross page boundaries,
  allowing the stack to extend beyond 256 bytes.

* The argument of the `ALLOC` opcode is interpreted as a signed byte
  in range [-128,+127].  To modify the stack pointer by larger
  amounts, one should use the `ADDV` or `SUBV` opcodes.  Note that it
  is very important to keep the stack pointer even.

* The argument of the `LSLW` and `STLW` opcodes is interpreted as an
  unsigned byte in range [0,255]. This means that these opdcodes can
  be used for accessing local variables stored at positive stack
  offsets. They no longer can access data stored below the stack
  head. Accessing data with offsets greater than 255 is possible using
  the slower `LSXW` and `STXW` instructions, or by computing their
  addresses in `vAC` and using the `DOKEA` or `DEEKA` instructions.

* The `PUSH` and `POP` opcodes only cross page boundaries when
  the stack pointer is even. Instructions `LDLW` and `STLW` only
  can access words whose two bytes belong to the same page. The 
  simplest way to ensure this is to keep the stack pointer even
  and only use even offsets in `LDLW` or `STLW`. If the stack
  contains long integer variables (4 bytes), it is convenient
  to go further and align the stack pointer on four bytes 
  boundaries.
  

**History:**
The first stack extension was the addition of a variable
byte `vSPH` located at address 0x04 in early ROMvX0s
(https://forum.gigatron.io/viewtopic.php?p=1995#p1995). This provides
the means to displace the stack into any page, but does not allow the
stack to exceed 256 byte.  The need for a true 16 bits stack was
expressed in (https://forum.gigatron.io/viewtopic.php?p=2053#p2053).
vCPU7 achieves this by displacing the `vTmp` scratch byte elsewhere in
page zero, freeing space after `vSP` to form a 16 bits word, and by
modifying the stack opcodes to allow them to cross page boundaries
when `vSPH` is nonzero.


### Conditional branches

Recall how the vCPU5 conditional branches `BEQ`, `BNE`, `BLT`, `BGT`,
`BLE`, and `BGE`, are encoded with a prefix byte `Bcc=0x35`, a
condition byte `EQ=0x3f`, `NE=0x72`, `LT=0x50`, `GT=0x4d`, `LE=0x56`,
or `GE=0x53`, and finally a byte containing the low byte of the target
address minus 2. Whereas vCPU5 only uses prefix `0x35` for conditional
branches, vCPU7 uses prefix `0x35` for a variety of opcodes that
tolerate a bit more overhead than the normal single-byte opcodes.

Meanwhile vCPU7 also recognizes the condition bytes as single-byte
opcodes to implement conditional branches to a 16 bit target address
encoded as two bytes LL and HH. The target address is `(HH*256)+((LL+2)&256)`.
The Jcc opcodes use the same space as the traditional `Bcc` opcodes.
JLT, JGE, and JGT are always faster than their Bcc counterparts.

An additional opcode `DBNE` is convenient for writing small
assembly code loops that iterate a predefined number of times. 

| Opcode | Encoding   |  Cycles   | Notes
| ------ | ---------- | --------- | -------
| `JEQ`  | `3f LL HH` |    24/26  | Jump if `vAC==0`
| `JNE`  | `72 LL HH` |    24/26  | Jump if `vAC!=0`
| `JLT`  | `50 LL HH` |    22/24  | Jump if `vAC<0`
| `JGE`  | `53 LL HH` |    22/24  | Jump if `vAC>=0`
| `JGT`  | `4d LL HH` | 22-24/26  | Jump if `vAC>0`
| `JLE`  | `56 LL HH` | 22-24/26  | Jump if `vAC<=0`
| `DBNE` | `7a VV LL` |    24/26  | Decrement byte [VV], jump if nonzero

**History:**:
Long conditional branches appeared in ROMvX0 around 2020.
vCPU7 encodes them with the vCPU5 condition bytes because these page 3
locations were free after moving all the vCPU5 branches into a
specific page for prefix `0x35`.


### Peek and poke alternatives

The following new instructions facilitate tasks that
are cumbersome using the vCPU5 instruction set. They often
permit to replace a long sequence of vCPU5 opcodes by
a shorter sequence that runs faster.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| DOKEA  | `3b VV`       | 28  | Store word `[VV..VV+1]` at address `[vAC]..[vAC]+1`
| DOKEQ  | `44 II`       | 22  | Store immediate `II` at address `[vAC]..[vAC]+1`
| DOKEI  | `35 63 HH LL` | 30  | Store immediate `HHLL` at address `[vAC]..[vAC]+1`
| DEEKA  | `3d VV`       | 30  | Load word at address `[vAC]..[vAC]+1` into `VV..VV+1`<br>(trashes `sysArgs7`)
| DEEKV  | `41 VV`       | 28  | Load word at address `VV..VV+1` into `vAC`
| POKEA  | `39 VV`     | 22  | Store byte `[VV]` at address `[vAC]`
| POKEQ  | `46 II`     | 20  | Store immediate `II` at address `[vAC]`
| PEEKA  | `e1 VV`     | 24  | Load byte at address `[vAC]` into `[VV]`
| PEEKV  | `dd VV`     | 28  | Load byte at address `VV` into `vAC`

**History:** :
Many of these instructions were discussed in the "New vCPU
instruction" thread and implemented by at67 in ROMvX0. The vCPU7
subset is motivated by the needs of the C compiler
(https://forum.gigatron.io/viewtopic.php?p=2053#p2053)
with naming conventions that are close to the ones
selected for ROMvX0.

Two additional instructions provide indexed access.

| Opcode |    Encoding    | Cycles | Function
| ------ | -------------- | -------| -------
| LDXW   | `6a VV LL HH`  | 28+30  | Load word at address `[VV]+$HHLL` into `vAC`<br>(trashes `sysArgs[5-7]`)
| STXW   | `6c VV LL HH`  | 28+30  | Store `vAC` into word at address `[VV]+$HHLL`<br>(trashes `sysArgs[5-7]`)

**History:** :
This draws on an earlier experience with indexed memory accesses
(https://forum.gigatron.io/viewtopic.php?p=2349#p2349). These opcodes
occasionally faster than direct address calculation followed by a peek
or poke opcode.  


### Moving data without changing vAC

The following instructions change page zero variables
without changing the contents of the accumulator `vAC`.

| Opcode | Encoding | Cycles  | Function
| ------ | -------- | ------- | -------
| MOVQB  | `48 VV II`    | 26 | Store immediate `II` into byte `VV`
| MOVQW  | `4a VV II`    | 28 | Store immediate `II` into word `VV..VV+1`
| MOVIW  | `b1 VV HH LL` | 30 | Store immediate `HHLL` into word `VV..VV+1`
| MOVW   | `bb YY XX`    | 36 | Copy word from `XX..XX+1` to `YY..YY+1`<br>(trashes `sysArgs7`)
| INCV   | `70 VV`       | 22 to 26 | Add 1 to word `VV..VV+1`
| NEGV   | `18 VV`       | 26 | Negates word `VV..VV+1`
| ADDSV  | `c6 VV II`    | 30 to 56 | Add signed immediate `II` to word `VV..VV+1`
| ADDV   | `66 VV`       | 30 | Add `vAC` contents to word `VV..VV+1`
| SUBV   | `68 VV`       | 30 | Subtract `vAC` contents from word `VV..VV+1`

Opcode `ADDSV` takes a signed byte as immediate argument and generally
runs in 30 cycles but incurs a penalty of 24/26 cycles when the
addition crosses a half-page boundary and possibly involves a carry.
Compared to alternatives such as `LDI;ADDV(VV)`, the amortized cost of
this penalty, about `|II|/5`, makes this opcode when `|II|` is smaller
than 80 or when the contents of `vAC` must be preserved.

**History:** Many of these instructions were discusssed in
(https://forum.gigatron.io/viewtopic.php?p=2053#p2053). The very
compact and useful implementation of `ADDV`, `SUBV`, and `ADDSV` are new.


### Comparison instructions

Four instructions leave in `vAC` a number that is less than, equal to,
or greater than zero depending on the comparison of the previous `vAC`
value with their arguments. These instructions replace the combination
of `CMPHS` or `CMPHU` with `SUBW` or `SUBI` but take less space and
run about as fast as a simple subtraction.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| CMPWS  | `d3 VV`  | 26 to 30 | Signed comparison of accumulator `vAC` and word `[VV..VV+1]`
| CMPWU  | `d6 VV`  | 26 to 30 | Unsigned  comparison of accumulator `vAC` and word `[VV..VV+1]`
| CMPIS  | `d9 II`  | 22 to 30 | Signed comparison of accumulator `vAC` and immediate `II`
| CMPIU  | `db II`  | 24 to 30 | Unsigned comparison of accumulator `vAC` and immediate `II`

**History:**
Replacing `CMPHU` and `CMPHS` by something faster and more compact was
considered desirable but had not been realized in just 30 cycles before.


### Miscellaneous

Instruction `LDSB` can be used to load a signed byte into `vAC`.
Instruction `ADDHI` adds a byte constant to `vACH` and can be
used before `ADDI` to add word constant to `vAC`.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| LDSB   | `6e VV`      | 24 | Load sign extended byte at address `VV` into `vAC`
| ADDHI  | `33 II`      | 16 | Add byte `0xII` to the high accumulator byte `vACH`.





### Multiplication and division

The following opcodes internally use the FSM machinery to split
relatively long operations into easily schedulable chunks of less than
30 cycles. All these operations make use of `sysArgs0..sysArgs7` as
working variables.

| Opcode |  Encoding  | Cycles     | Function
| ------ | ---------- | -----------| -------
| MULW   | `35 3d VV` | ~= 500     | Multiply accumulator `vAC` by word `[VV..VV+1]`<br>(trashes `sysArgs[0-7]`)
| MULQ   | `7d KK`    | 44 to 152  | Multiply accumulator `vAC` by small immediate<br>(trashes `sysArgs[0-7]`)
| RDIVU  | `35 3b VV` | ~= 1100    | Unsigned division of word `VV..VV+1` by `vAC`<br>(trashes `sysArgs[0-7]`)
| RDIVS  | `35 39 VV` | ~= 1200    | Signed division of word `VV..VV+1` by `vAC`<br>(trashes `sysArgs[0-7]`)

The multiplication opcodes `MULW` and `MULQ` leave the low
sixteen bits of the product in `vAC`.

The division opcode `RDIVU` and `RDIVS` only work reliably
when the divisor `vAC` is nonzero. They leave the quotient
in `vAC` and the remainder in `sysArgs4..sysArgs5`.

The argument of the `MULQ` opcode is a single byte whose bits are interpreted
as a micro-program that specifies shifts, additions, and subtractions.
The following python program simulates its operation:

```python
def mulq(vAC, KK):
    tmp = vAC
    vAC <<= 1
    while KK & 0xff:
        if KK & 0x80:
            vAC <<= 1; KK <<= 1
        elif KK & 0x40:
            vAC += tmp; KK <<= 2
        else:
            vAC -= tmp; KK <<= 3
    return vAC
```

For instance `KK=0b01000000` mutiplies by 3, `KK=0b10100000` by 5,
`KK=0b01100000` by 6, `KK=0b11001000` by 7, etc.  It is recommended to
use `MULQ` for all small multiplication except for the multiplications
by 2 and 4 which are better implemented with `LSLW`.
The following python code builds a table that can be used
to convert small multipliers into `MULQ` arguments and
computes the corresponding execution times:
```python
def mulq_table():
    mulq_tbl, mulq_cyc = {}, {}
    for k in range(256):
        vAC, KK, cycles = 2, k, 44
        while KK & 0xff:
            if KK & 0xc0 == 0xc0:
                cycles += 28; KK <<= 2; vAC <<= 2
            elif KK & 0xc0 == 0x80:
                cycles += 18; KK <<= 1; vAC <<= 1
            elif KK & 0xc0 == 0x40:
                cycles += 24; KK <<= 2; vAC += 1
            else:
                cycles += 24; KK <<= 3; vAC -= 1
        if vAC not in mulq_tbl or cycles < mulq_cyc[vAC]:
            if vAC not in (0,1,2,4):
                mulq_tbl[vAC], mulq_cyc[vAC] = k, cycles
    return mulq_tbl, mulq_cyc
```

**History:**
A SYS call to perform 16 bits multiplications and divisions was
offered in ROMvX0 and then DEV6ROM. In DEV7ROM, these syscalls have
been reimplemented with FSM with more speed and better functionality
(less setup, 16 bits division instead of 15 bits division). These
opcodes share the same implementation but demand even less setup.


### Copy instructions

These copy instructions can cross page boundaries and deal with
misaligned data.  They use `sysArgs2..sysArgs7` as working buffer and
therefore should not be used to copy data from or to arbitrary
positions in the sysArgs array. It is however possible to reliably
copy up to five bytes to or from `sysArgs0` (only!).


| Opcode |  Encoding     | Cycles  | Function
| ------ | ------------- | --------| -------------
| COPY   | `35 cb`       | (notes) | Copy `vACL` bytes from `[vT3]..` to `[vT2]..`.<br>(trashes `sysArgs[2-7]`)
| COPYN  | `35 cf NN`    | (notes) | Copy `NN` bytes from `[vT3]..` to `[vT2]..`.<br>(trashes `sysArgs[2-7]`)
| COPYS  | `35 02 VV NN` | (notes) | Copy `NN&127` bytes from `[vSP]` to `VV` (NN<128) or back (NN>128).<br>(trashes `sysArgs[2-7]`)


All three instructions use the same underlying code that copies up to
256 bytes using register `vT3` as a source address register and `vT2`
as a destination address register.  On return, both register `vT2` and
`vT3` are incremented past the last copied byte, which is useful for
chaining copy operations.

For instance, instruction `COPY` treats `vAC` as the total number of
bytes to copy and returns the number of bytes left to copy after
copying at most 256 bytes. Therefore one can simply loop to copy
longer sequences, as in the following piece of code
```
    # Copy vAC bytes from [T3] to [T2]
    label('loop')
    COPY()
    JNE('loop')
```

Instruction `COPYN` obtains the number of bytes to copy from its
argument saving the need for an additional instruction to load it into
`vAC` (a zero byte stands for a 256 bytes copy).
Instruction `COPYS` additionally sets up `vT2` and `vT3` to
help transfering data to and from the stack. It can be used together
with the `ALLOC` instruction to push or pop multiple values on the
stack at once.

Like most long vCPU7.md instructions, the memory copy instructions
rely on the FSM mechanism (https://forum.gigatron.io/viewtopic.php?t=403)
to split the job into pieces of at most 30 cycles. The code burst
copies four bytes when no page crossings are involved. Otherwise it
reverts to a slower byte-per-byte copy that can cross page
boundaries. Peak speed is 10 bytes copied per scanline. For
comparison, `SYS_CopyMemory` can manage 12 bytes per scanline but has
longer setup times and cannot cross page boundaries.


**History:**
The need to copy memory quickly has long been recognized.
Historical progress includes the `SYS_CopyMemory` call of DEV6ROM
(https://forum.gigatron.io/viewtopic.php?t=302)
which is fast but inconvenient and the `NCOPY` instruction 
initially written for ROMvX0 which is convenient but substantially slower.  
The FSM framework made it possible to have both.


### Long arithmetic

Long arithmetic instructions are implemented with the FSM framework
and use `sysArgs5..sysArgs7` as working memory. Most of these
instructions implicitly address the 32 bits long accumulator `vLAC`
and use `vAC` to specify the address of their argument.  Long integers
cannot cross page boundaries. As usual the signed comparisons leave in
`vAC` a number that is less than, equal to, or greater than zero ready
for conditional jump opcodes.

| Opcode |  Encoding  | Cycles      | Function
| ------ | ---------- | ----------- | -------
| LDLAC  | `35 1e`    | 36          | Load long `[vAC]..[vAC]+3` into long accumulator `vLAC`
| STLAC  | `35 20`    | 34          | Store long accumulator `vLAC` into `[vAC]..[vAC]+3`
| MOVL   | `35 db YY XX` | 30+30    | Copy long from `XX..XX+3` to `YY..YY+3`<br>(trashes `sysArgs[0-7]`)
| LEEKA  | `35 32 XX` | 28+34       | Copy long from `[vAC]..[vAC]+3` to `XX..XX+3`<br>(trashes `sysArgs[2-7]`)
| LOKEA  | `35 34 XX` | 28+34       | Copy long from `XX.XX+3` to `[vAC]..[vAC]+3`<br>(trashes `sysArgs[2-7]`)
| ADDL   | `35 00`    | 22+30+28    | Add long `[vAC]..[vAC]+3` to long accumulator `vLAC`<br>(trashes `sysArgs[6-7]`)
| SUBL   | `35 04`    | 22+28+28    | Subtract long `[vAC]..[vAC]+3` from long accumulator `vLAC`<br>(trashes `sysArgs[6-7]`)
| ANDL   | `35 06`    | 22+28       | Bitwise and of `[vAC]..[vAC]+3` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| ORL    | `35 08`    | 22+28       | Bitwise or of `[vAC]..[vAC]+3` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| XORL   | `35 0a`    | 22+28       | Bitwise xor of `[vAC]..[vAC]+3` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| CMPLS  | `35 14`    | max 22+20+24| Signed compare long accumulator `vLAC` with `[vAC]..[vAC]+3`<br>(trashes `sysArgs7`)
| CMPLU  | `35 16`    | max 22+20+24| Unsigned compare long accumulator `vLAC` with `[vAC]..[vAC]+3`<br>(trashes `sysArgs7`)

Three additional instructions operate on long integers in page zero
without changing the contents of either `vAC` or `vLAC` (unless of
course their argument specifies addresses that overlap `vAC`
or `vLAC`.

| Opcode |  Encoding  | Cycles     | Function
| ------ | ---------- | ---------- | -------
| INCVL  | `35 23 VV` | 22+16..26  | Increment long `VV..VV+3`<br>(trashes `sysArgs[67]`)
| NEGVL  | `35 0c VV` | 28+24      | Negate long `VV..VV+3`<br>(trashes `sysArgs[67]`)
| NOTVL  | `35 d3 VV` | 28+24      | Complement long `VV..VV+3`<br>(trashes `sysArgs[67]`)
| LSLVL  | `35 10 VV` | 28+30      | Left shift long  `VV..VV+3`<br>(trashes `sysArgs[67]`)

**History:**
These are improvements of the long arithmetic opcodes
implemented for ROMvX0 ia while ago. Thanks to the FSM framework,
they are implemented as easy-to-schedule chunks and avoid the hidden
but severe overhead of long monolithic instructions.


### Extended arithmetic, shifts, and floating point

A couple instruction operate on the extended 40 bits accumulator `vLAX`
whose upper 32 bits overlate the long accumulator `vLAC`.

| Opcode | Encoding      | Cycles     | Function
| ------ | ----------    | ---------- | -------
| NEGX   | `35 0e`       | 22+14+24   | Negate the extended accumulator `vLAX`
| MACX   | `35 1c`       | 394 to 842 | Add `vACL` (8 bits) times `sysArgs[0..4]` to `vLAX`<br>(trashes `sysArgs[5..7]`, `vACH`)
| LSRXA  | `35 18`       | 42 to 322  | Right shift `vLAX` by `vAC & 0x3f` positions<br>(trashes `sysArgs[6..7]`, `vAC`)
| LSLXA  | `35 12`       | 38 to 415  | Left shift `vLAX` by `vAC & 0x3f` positions<br>(trashes `sysArgs[6..7]`, `vAC`)
| RORX   | `35 1a`       | 198        | Right rotate `vLAX` from/into bit 0 of `vAC`.<br>(trashes `sysArgs[6..7]`, `vAC`)

The opcode `MACX` is a building block for both the long and the
floating point multiplication routines. It multiplies a 32 bits number (in `sysArgs[0..4]`)
by a 8 bit number in `vAC` and adds the product to the extended accumulator `vLAX`.

Opcodes `LSRXA` and `LSLXA` respectively shift the extended
accumulator right or left by `vAC & 0x3f` positions.  They are most
efficient when `vAC` contains a multiple of eight because such a shift
can be implemented by displacing or clearing entire bytes. As usual on
the Gigatron, finer shift amounts are implemented using tables (right
shift) or repeated additions (left shift).

Opcode `RORX` implements a 41 bits rotation that encompasses
the 40 bits of `vLAX` and the least significant bit of `vAC`,
as illustrated below:
```
RORX      .-->--[LAX+4...LAX]-->--.
          '--<------[VAC0]-----<--'
```

A couple additional opcodes help with floating point numbers
encoded with the same 40 bits floating point format used
by the once popular Microsoft basic interpreters.


| Opcode | Encoding      | Cycles     | Function
| ------ | ----------    | ---------- | -------
| MOVF   | `35 dd YY XX` | 30+38      | Copy fp number from `XX..XX+4` to `YY..YY+4`<br>(trashes `sysArgs[0..7]`)
| LDFAC  | `35 27`       | typ 72     | Load fp number `[vAC]..[vAC]+4` into float accumulator<br>(trashes `vAC` `vT3` `sysArgs[5-7]`)
| STFAC  | `35 25`       | typ 66     | Store float accumulator into fp var `[vAC]..[vAC]+4`<br>(trashes `vAC` `sysArgs[5-7]`)
| LDFARG | `35 29`       | typ 72     | Load floating point argument `[vAC]..[vAC]+4`<br>(trashes `vAC` `sysArgs[5-7]`)

Opcode `MOVF` merely moves five consecutive bytes in page zero.

Opcodes `LDFAC` and `STFAC` respectively unpack and pack a floating
point number into a virtual floating point accumulator composed of
registers `vFAS` for the sign (bit 7), `vFAE` for the
exponent, and `vLAX` for the mantissa.  Because five bytes floating
point numbers do not naturally align on page boundaries, opcodes
`LDFAC` and `STFAC` can deal with floating point numbers that cross
page boundaries, at the expense of many additional cycles.

Opcode `LDFARG` is solely intended as a helper for the floating point
emulation routines. It unpacks a second floating point number by storing
its mantissa in `sysArgs[0..4]` and its exponent in the low byte of `vT2`.
Bit 0 of `vFAS` then indicates whether this number has a sign different
from the number loaded by `LDFAC` which is stored in bit 7 of `vFAS`.

### Graphics

Two opcodes, `FILL` and `BLIT` are useful for creating graphics.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | ------ | ----
| FILL   | `35 4a`  | max `36+h*(24+ceil(w/12)*28)` | Fill a rectangular area<br>(trashes sysArgs[4-7])
| BLIT   | `35 48`  | max `72+h*(20+ceil(w/6)*56)`  | Copy a rectangular area<br>(trashes sysArgs[0-7], vLAC)

Both opcodes see the Gigatron memory as a 256x256 array of bytes, with both rows
and columns wrapping around, and operate on subarrays of this array, 
defined by a range of rows (y coordinates) and a range of columns (x coordinates).
Depending on the contents of the video table, the screen buffer can also be set up 
as a subarray defined by a range of rows and a range of columns. 

Both opcodes change the contents of a destination subarray whose top-left corner 
is provided  in register `vT2`, y coordinate in the high byte, x coordinate in the low byte,
and whose size is provided by register `vAC`, height im the high byte, and width in the low byte.
A width or height of 0 means 256.

* Opcode `FILL` writes the low byte of register `vT3` into all bytes
  in the destination subarray. This is useful to clear the screen or
  display filled rectangles. The peak speed of 60 bytes per scanline
  is achieved when the destination width is a multiple of 12. It takes
  28 cycles to fill 12 consecutive bytes in a row. Excess bytes
  typically take another chunk of 28 cycles. A special mode saves time
  for vertical lines, that is, width 1.

* Opcode `BLIT` copies an equally sized source subarray into the
  destination subarray. Register `vT3` describes the coordinates of
  the top-left corner of the source subarray, y coordinate in the high
  byte, and x coordinate in the low byte. The peak speed of 15 bytes
  per scanline is achieved when the width is a multiple of 6. When the
  subarray height is less than 128, the copy operation is ordered to
  ensure that it does not overwrite source bytes before using
  them. However this fails when both subarrays have identical y
  coordinate and a width of 256.


### Context and interrupts

Two instructions, `VSAVE` and `VRESTORE` respectively save and restore
the full virtual interpreter context. A third instruction `EXBA` is
useful to atomically read-modify-write.


|  Opcode  | Encoding    | Cycles  | Function
| -------- | ----------- | ------- | -------
| VSAVE    | `35 2b`     | ~104    | save full vCPU context into xxe0-xxff
| VRESTORE | `35 2d`     | ~126    | restore vCPU context saved in xxe0-xxff
| EXBA     | `35 31 ii`  |  28+18  | perform ii->[vAC]->vAC atomically

Both `VSAVE` and `VRESTORE` take a page number `xx` in the low byte of
register `vAC` and use address range `xxe0-xxff` to save or restore
the context as follows:
```
 xx00+0xe0: vAC
     +0xe2: vPC, vLR, vSP
     +0xe8: vLAC, vT2, vT3
     +0xf0: sysArgs[0-7]
     +0xf8: sysFn
     +0xfa: vFAS, vFAE, vLAX0
     +0xfd: vCpuSelect
     +0xfe: irqFlag   (see below)
     +0xff: irqMask   (see below)
```

A virtual interrupt condition occurs whenever byte `frameCount` wraps
around to zero. The new system variable `vIrqCtx_v7` (0x1f5) controls
what happens when this is the case.

* When `vIrqCtx_v7` is zero, virtual interrupts are fully backward
  compatible and work exactly as described in the document
  [Interrupts.txt](Interrupts.txt). The interrupt handler should then
  return with the usual LUP sequence, making sure to restore the value
  of all registers they have used besides vAC and vPC.

* When `vIrqCtx_v7` is nonzero, a virtual interrupt saves the full
  context at offsets 0xe0-0xff in the page indicated by `vIrqCtx_v7`
  as if the `VSAVE` instruction had been invoked. Interrupt handlers
  should then return using the VRESTORE opcode.  However, interrupt
  are inhibited when byte `irqMask` at offset 0xff in the context page
  is nonzero. Flag `irqFlag` indicates whether this has happened.
  
Byte `irqMask` in the context record is automatically set to a nonzero
value when the context is saved by an interrupt or by `vSAVE`, and is
cleared by `VRESTORE`. This feature prevents another virtual interrupt
to occur before the completion of the interrupt handler. When a
virtual interrupt is inhibited because `vIrqMask` is nonzero, byte
`irqFlag` in the context record receives a copy of `irqMask`.

Opcode `VRESTORE` can also atomically adjusts the value of
`frameCounter` by adding `vACH` and saturating to `0xff` if there is a
carry. This is useful in the context of an interrupt because one can
arrange for another interrupt to occur `x` frames after the current
interrupt by simply setting `vACH` to `-x` before calling `VRESTORE`,
accounting for the duration of the interrupt handler as well.

Example: the following code causes `0xc0-c1` to count the number
of elapsed seconds, saving the context in `0x7fe0-7fff`:
```
   setup:   LDWI(0x7fff);POKEQ(1);LDWI(0x1f5);POKEQ(0x7f) # mask virq
            INC(vAC);DOKEI(handler)                       # set handler
            LDWI(0x7fff);POKEQ(0)                         # unmask virq
            RET()
   handler: INCV(0xc0)
            LDWI(0xc47f);VRESTORE()      # 0xc4 == -60 frames
```

Note that the old method is still the fastest way to handle
interrupts.  Although it brings convenience and safety, saving and
restoring a full context takes more time. However, manually saving a
partial context after an old-style interrupt can quickly become slower
than using the new style interrupts. New style interrupts have the
added benefit to leave the `irqSave` variables (0x30-0x35)
unchanged. Since these variables are frequently used by programs that
predate ROMv5a, the new-style interrupts are in fact easier to
retrofit into an older program.

For instance one can start WozMon (by pressing key `W` in the main menu),
setup this same interrupt handler, and observe `c0.c1` increase every second.
This would crash with old-style interrupts because WozMon also uses
locations 0x30-35 for its own purposes.
```
8a0:70 c0 11 7f c4 35 2b         # INCV($c0) LDWI($c47f) VRESTORE()
 08A0: xx
7fff:1                           # set irqMask to mask interrupts
 7FFF: xx
1f5:7f a0 8                      # vIrqCtx_v7 and vIRQ
 01F5: 00
7fff:0                           # unmask interrupts
 7FFF: 01
c0.c1
 C0: xx xx
```

Instruction `EXBA` atomically sets the byte addressed by `vAC` to its
immediate argument while saving its previous values ito `vAC`.  This
is useful because the two operations happen without intervening
virtual interrupts. For instance one can reset `frameCount` without
losing a tick as follows:
```
   LDI('frameCount`); EXBA(0)                   # read and reset framecount
   STW(LAC);MOVQW(0,LAC+2)                      # copy old framecount into LAC
   LDWI('clock');ADDL();STLAC()                 # add it to the long var 'clock'
```
Instructions `VSAVE` and `VRESTORE` can also be used to organize
multiple execution threads. Instruction `EXBA` can then be used for
thread synchronization.


### Reset instruction and system variable changes.

Instruction `RESET` is only used by the reset stub at address `0x1f0`.
This is a two bytes instruction whose exact encoding is subject to change.
Its sole purpuse is to make locations `0x1f2-0x1f5` available for other purposes.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| RESET  | private  | n/a    | Soft reset

This instruction was implemented to shorten the reset sequence at
address `0x1f0` which used to be six bytes long and is now only two
bytes long. The locations `0x1f2-0x1f5` can then be used for other
purposes such as `vIrqCtx_v7` or `ledTempo_v7`.

Variable `ledTempo` has been displaced to a new location
`ledTempo_v7` at address 0x1f3. The old location is now used by the
private variable `vTmp` which is used as a scratch variable by the
implementation of many vCPU instructions. This means that writing
anything into the old `ledTempo` location is harmless but will be
quickly overwritten by any of the many vCPU opcodes
whose implementation uses `vTmp`.

Some private system variables have also been changed to make space for
two critical variables used by `dev128k7.rom` to separate the memory
bank used for video output and the memory bank seen by the vCPU, which
was the project that started the whole DEV7ROM adventure.  The led
timer has been moved to address 0x1f4, and, on `dev128k7.rom`, the
third byte of the entropy counter has been moved to address 0x1f2.
Their former locations are now used to cache the control bits that
should be used during video generation and during vcpu
execution. Although overwriting these variables can crash the
Gigatron, short of a bug, legacy programs are unlikely to write to
these locations because anything written there used to be quickly
overwritten by the gigatron firmware.

Except for `ledTempo` discussed above, all other public system
variables documented in `interface.json` remain at the same location
and perform the same task. For instance, the recommended way to
control the LEDs is to stop the sequencer by setting `ledState_v2` to
a positive value (e.g. 1) and writing the desired led state into the
low four bits of variable `xoutMask` (see program `BASIC/LEDS.gtb`).
