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


### Long conditional branches

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

| Opcode | Encoding   |  Cycles   | Notes
| ------ | ---------- | --------- | -------
| `JEQ`  | `3f LL HH` |    24/26  | Jump if `vAC==0`
| `JNE`  | `72 LL HH` |    24/26  | Jump if `vAC!=0`
| `JLT`  | `50 LL HH` |    22/24  | Jump if `vAC<0`
| `JGE`  | `53 LL HH` |    22/24  | Jump if `vAC>=0`
| `JGT`  | `4d LL HH` | 22-24/26  | Jump if `vAC>0`
| `JLE`  | `56 LL HH` | 22-24/26  | Jump if `vAC<=0`

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
| DOKEI  | `35 62 HH LL` | 30  | Store immediate `HHLL` at address `[vAC]..[vAC]+1`
| DEEKA  | `3d VV`       | 30  | Load word at address `[vAC]..[vAC]+1` into `[VV..VV+1]`<br>(trashes `sysArgs7`)
| DEEKV  | `41 VV`       | 28  | Load word at address `[VV]..[VV]+1` into `vAC`
| POKEA  | `39 VV`     | 22  | Store byte `[VV]` at address `[vAC]`
| POKEQ  | `46 II`     | 20  | Store immediate `II` at address `[vAC]`
| PEEKA  | `e1 VV`     | 24  | Load byte at address `[vAC]` into `[VV]`
| PEEKV  | `dd VV`     | 28  | Load byte at address `[VV]` into `vAC`

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
| MOVQB  | `48 VV II`    | 26 | Store immediate `II` into byte `[VV]`
| MOVQW  | `4a VV II`    | 28 | Store immediate `II` into word `[VV..VV+1]`
| MOVIW  | `b1 VV HH LL` | 30 | Store immediate `HHLL` into word `[VV..VV+1]`
| MOVW   | `bc YY XX`    | 36 | Copy var from `[XX..XX+1]` to `[YY..YY+1]`<br>(trashes `sysArgs7`)
| INCV   | `70 VV`       | 22 to 28 | Add 1 to word `[VV..VV+1]`
| ADDV   | `66 VV`       | 30 | Add `vAC` contents to word `[VV..VV+1]`
| SUBV   | `68 VV`       | 30 | Subtract `vAC` contents from word `[VV..VV+1]`
| ADDIV  | `35 7d II VV` | 38 to 40 | Add immediate `II` to word `[VV..VV+1]`
| SUBIV  | `35 9c II VV` | 38 to 40 | Subtract immediate `II` from word `[VV..VV+1]`
| NEGV   | `18 VV`       | 26 | Negates word `[VV..VV+1]`

**History:**
Many of these instructions were discusssed in
(https://forum.gigatron.io/viewtopic.php?p=2053#p2053). The very
compact and useful implementation of `ADDV` and `SUBV` is new.


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

Instructions `LDNI` and `LDSB` can be used to load a signed byte into `vAC`.
Instruction `ADDHI` adds a byte constant to `vACH` and can be
used before `ADDI` to add word constant to `vAC`.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| LDNI   | `78 II`      | 16 | Load negative immediate `0xffII` into `vAC`
| LDSB   | `6e VV`      | 24 | Load signed extended byte `[VV]` into `vAC`
| ADDHI  | `33 II`      | 16 | Add byte `0xII` to the high accumulator byte `vACH`.

**History:**
A variant of `LDNI` exists in ROMvX0 but negates its argument (slower)
instead of using a 2-complements approach. In order to make it as fast
as possible, this is implementated entirely in page 3 just like `LDI`
and `LDWI`.



### Multiplication and division

The following opcodes internally use the FSM machinery to split
relatively long operations into easily schedulable chunks of less than
30 cycles. All these operations make use of `sysArgs0..sysArgs7` as
working variables.

| Opcode |  Encoding  | Cycles     | Function
| ------ | ---------- | -----------| -------
| MULW   | `35 3d VV` | ~= 500     | Multiply accumulator `vAC` by word `[VV..VV+1]`<br>(trashes `sysArgs[0-7]`)
| MULQ   | `7d KK`    | 44 to 152  | Multiply accumulator `vAC` by small immediate<br>(trashes `sysArgs[0-7]`)
| RDIVU  | `35 3b VV` | ~= 1100    | Unsigned division of word `[VV..VV+1]` by `vAC`<br>(trashes `sysArgs[0-7]`)
| RDIVS  | `35 39 VV` | ~= 1200    | Signed division of word `[VV..VV+1]` by `vAC`<br>(trashes `sysArgs[0-7]`)

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
    while KK != 0:
        if KK & 0x80 == 0x80:
            vAC <<= 1; KK <<= 1
        elif KK & 0xc0 == 0x40:
            vAC += tmp; KK <<= 2
        else KK & 0xe0 == 0x20:
            vAC -= tmp; KK <<= 3
```

For instance `KK=0b01000000` mutiplies by 3, `KK=0b10100000` by 5,
`KK=0b01100000` by 6, `KK=0b11001000` by 7, etc.  The execution time
is composed of a 44 cycles overhead, 14 to 18 cycles per shift, and 24
cycles per addition or subtraction. It is recommended to use `MULQ`
for all small multiplication except for the multiplications by 2 and 4
which are better implemented with `LSLW`.

**History:**
A SYS call to perform 16 bits multiplications and divisions was
offered in ROMvX0 and then DEV6ROM. In DEV7ROM, these syscalls have
been reimplemented with FSM with more speed and better functionality
(less setup, 16 bits division instead of 15 bits division). These
opcodes share the same implementation but demand even less setup.


### Copy instructions

These copy instructions can cross page boundaries and deal with
misaligned data.  They use `sysArgs0..sysArgs7` as working buffer and
therefore should not be used to copy data from or to arbitraty
positions in the sysArgs array. It is however possible to reliably
copy up to five bytes to or from `sysArgs0` (only!).


| Opcode |  Encoding  | Cycles     | Function
| ------ | ---------- | -----------| -------
| COPY   | `35 cb`    |  (notes)   | Copy `vACL` bytes from `[vT3]..` to `[vT2]..`.<br>(trashes `sysArgs[0-7]`)
| COPYN  | `35 cf NN` |  (notes)   | Copy NN bytes from `[vT3]..` to `[vT2]..`.<br>(trashes `sysArgs[0-7]`)

Like most long vCPU7.md instructions, the memory copy instructions
rely on the FSM mechanism (https://forum.gigatron.io/viewtopic.php?t=403)
to split the job into pieces of at most 30 cycles. The code burst
copies four bytes when no page crossings are involved. Otherwise it
reverts to a slower byte-per-byte copy that can cross page
boundaries. Peak speed is 10 bytes copied per scanline. For
comparison, `SYS_CopyMemory` can manage 12 bytes per scanline but has
longer setup times and cannot cross page boundaries.

On return, both `[vT2]` and `[vT3]` are incremented past the last
copied byte, which is useful for chaining copy operations.
Instruction `COPY` additionally treats `vAC` as the total number of
bytes to copy and returns the number of bytes left to copy after
copying at most 256 bytes. Therefore one can simply loop to copy
longer sequences, as in the following piece of code
```
   # Copy vAC bytes from [T3] to [T2]
   label('loop')
   COPY()
   JNE('loop')
```

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
instructions implicitly address the long accumulator `vLAC` and use
`vAC` to specify the address of their argument.  Long integers cannot
cross page boundaries. As usual the signed comparisons leave in `vAC`
a number that is less than, equal to, or greater than zero ready for
conditional jump opcodes.

| Opcode |  Encoding  | Cycles      | Function
| ------ | ---------- | ----------- | -------
| LDLAC  | `35 1e`    | 38          | Load long `[vAC]..[vAC+3]` into long accumulator `vLAC`
| STLAC  | `35 20`    | 38          | Store `vLAC` into `[vAC]..[vAC+3]` into long accumulator `vLAC`
| MOVL   | `35 db YY XX` | 30+30    | Copy long from `[XX..XX+3]` to `[YY..YY+3]`<br>(trashes `sysArgs[0-7]`)
| ADDL   | `35 00`    | 22+30+28    | Add long `[vAC]..[vAC+3]` to long accumulator `vLAC`<br>(trashes `sysArgs[5-7]`)
| SUBL   | `35 04`    | 22+28+28    | Subtract long `[vAC]..[vAC+3]` from long accumulator `vLAC`<br>(trashes `sysArgs[5-7]`)
| ANDL   | `35 06`    | 22+28       | Bitwise and of `[vAC]..[vAC+3]` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| ORL    | `35 08`    | 22+28       | Bitwise or of `[vAC]..[vAC+3]` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| XORL   | `35 0a`    | 22+28       | Bitwise xor of `[vAC]..[vAC+3]` with long accumulator `vLAC`<br>(trashes `sysArgs7`)
| CMPLS  | `35 14`    | max 22+20+24| Signed compare long accumulator `vLAC` with `[vAC]..[vAC+3]`<br>(trashes `sysArgs7`)
| CMPLU  | `35 16`    | max 22+20+24| Unsigned compare long accumulator `vLAC` with `[vAC]..[vAC+3]`<br>(trashes `sysArgs7`)

Three additional instructions operate on long integers in page zero
without changing the contents of either `vAC` or `vLAC` (unless of
course their argument specifies addresses that overlap `vAC`
or `vLAC`.

| Opcode |  Encoding  | Cycles     | Function
| ------ | ---------- | ---------- | -------
| INCVL  | `35 23 VV` | 22+16..26  | Increment long `[VV..VV+3]`<br>(trashes `sysArgs[67]`)
| NEGVL  | `35 0c VV` | 28+24      | Negates long `[VV..VV+3]`<br>(trashes `sysArgs[67]`)
| LSLVL  | `35 10 VV` | 28+30      | Left shift long  `[VV..VV+3]`<br>(trashes `sysArgs[67]`)

**History:**
These are improvements of the long arithmetic opcodes
implemented for ROMvX0 ia while ago. Thanks to the FSM framework,
they are implemented as easy-to-schedule chunks and avoid the hidden
but severe overhead of long monolithic instructions.


### Extended arithmetic, shifts, and floating point

A small number of opcodes deal with floating point numbers in
Microsoft format. Because the five bytes long floating point numbers
do not naturally align on page boundaries, crossing page boundaries
is allowed by the `LDFAC` and `STFAC` functions at the cost of
additional cycles. These functions work with a virtual floating
point accumulator composed of registers `vFAS` for the sign,
`vFAE` for the exponent, and `vLAX` for the mantissa.

| Opcode | Encoding      | Cycles     | Function
| ------ | ----------    | ---------- | -------
| MOVF   | `35 dd YY XX` | 30+38      | Copy fp number from `[XX..XX+4]` to `[YY..YY+4]`<br>(trashes `sysArgs[0..7]`)
| LDFAC  | `35 27`       | typ 72     | Load fp number `[vAC]..[vAC]+4` into float accumulator<br>(trashes `vAC` `vT3` `sysArgs[5-7]`)
| STFAC  | `35 25`       | typ 66     | Store float accumulator into fp var `[vAC]..[vAC]+4`<br>(trashes `vAC` `sysArgs[5-7]`)

Three shift instructions operate on the 40 bits extended accumulator `vLAX`.

| Opcode | Encoding      | Cycles     | Function
| ------ | ----------    | ---------- | -------
| LSRXA  | `35 18`       | 54 to 382  | Right shift `vLAX` by `vAC & 0x3f` positions
| LSLXA  | `35 12`       | 36 to 422  | Left shift `vLAX` by `vAC & 0x3f` positions
| RORX   | `35 1a`       | 198        | Right rotate `vLAX` from/into bit 0 of `vAC`

The following picture illustrates how `RORX` rotate bits:
```
RORX      .-->--[LAX+4...LAX]-->--.
          '--<------[VAC0]-----<--'
```

The following instructions are mostly used to accelerate the floating point runtime.
See the source code comments for a more precise documentation.

| Opcode | Encoding      | Cycles     | Function
| ------ | ----------    | ---------- | -------
| LDFARG | `35 29`       | typ 72     | Load floating point argument `[vAC]..[vAC]+4`
| NEGX   | `35 0e`       | 22+14+24   | Negate extended accumulator `vLAX`
| MACX   | `35 1c`       | 394 to 842 | Adds the product of `vACL` (8 bits) by `sysArgs[0..4]` (32 bits) to `vLAX` (40 bits)

**History:**
These extended arithmetic and floating point support instructions
would have been very hard to code without the FSM framework.
They have been selected after profiling the GLCC floating point runtime.


### Reset instruction

Instruction `RESET` is only used by the reset stub at address `0x1f0`.
This is a two bytes instruction whose exact encoding is subject to change.
Its sole purpuse is to make locations `0x1f2-0x1f5` available for other purposes.

| Opcode | Encoding | Cycles | Function
| ------ | -------- | -------| -------
| RESET  | private  | n/a    | Soft reset


**History:** This instruction was implemented to shorten the reset
sequence at address `0x1f0` which used to be
`LDI(SYS_Reset_88);STW(sysFn);SYS(88)` (six bytes) and is now only two
bytes long. This frees locations `0x1f2-0x1f5` which now contain
values formerly held in nonpublic locations of page zero (`entropy+2`,
`ledTimer`).  The public variable `ledTempo` has also been displaced
there under the name `ledTempo_v7` to make space for the displaced
`vTmp`. Old programs can still safely write into the old `ledTempo`
location, but anything they write will be overwritten whenever an
opcode uses the scratch location `vTmp`.  Note that the public
variable `ledState_v2`, which can in fact be used to stop the led
sequence, is still in its usual place.
