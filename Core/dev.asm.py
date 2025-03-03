#!/usr/bin/env python3
#-----------------------------------------------------------------------
#
#  Core video, sound and interpreter loop for Gigatron TTL microcomputer
#
#-----------------------------------------------------------------------
#
#  Main characteristics:
#
#  - 6.25 MHz clock
#  - Rendering 160x120 pixels at 6.25MHz with flexible videoline programming
#  - Must stay above 31 kHz horizontal sync --> 200 cycles/scanline
#  - Must stay above 59.94 Hz vertical sync --> 521 scanlines/frame
#  - 4 channels sound
#  - 16-bits vCPU interpreter
#  - 8-bits v6502 emulator
#  - Builtin vCPU programs (Snake, Racer, etc) loaded from unused ROM area
#  - Serial input handler, supporting ASCII input and two game controller types
#  - Serial output handler
#  - Soft reset button (keep 'Start' button down for 2 seconds)
#  - Low-level support for I/O and RAM expander (SPI and banking)
#
#-----------------------------------------------------------------------
#
#  ROM v2: Mimimal changes
#
#  DONE Snake color upgrade (just white, still a bit boring)
#  DONE Sound continuity fix
#  DONE A-C- mode (Also A--- added)
#  DONE Zero-page handling of ROM loader (SYS_Exec_88)
#  DONE Replace Screen test
#  DONE LED stopped mode
#  DONE Update font (69;=@Sc)
#  DONE Retire SYS_Reset_36 from all interfaces (replace with vReset)
#  DONE Added SYS_SetMemory_54 SYS_SetVideoMode_80
#  DONE Put in an example BASIC program? Self list, self start
#  DONE Move SYS_NextByteIn_32 out page 1 and rename SYS_LoaderNextByteIn_32
#       Same for SYS_PayloadCopy_34 -> SYS_LoaderPayloadCopy_34
#  DONE Update version number to v2a
#  DONE Test existing GT1 files, in all scan line modes
#  DONE Sanity test on HW
#  DONE Sanity test on several monitors
#  DONE Update version number to v2
#
#-----------------------------------------------------------------------
#
#  ROM v3: New applications
#
#  DONE vPulse width modulation (for SAVE in BASIC)
#  DONE Bricks
#  DONE Tetronis
#  DONE TinyBASIC v2
#  DONE TicTacToe
#  DONE SYS spites/memcpy acceleration functions (reflections etc.)
#  DONE Replace Easter egg
#  DONE Update version number to v3
#
#-----------------------------------------------------------------------
#
#  ROM v4: Numerous small updates, no new applications
#
#  DONE #81 Support alternative game controllers (TypeC added)
#  DONE SPI: Setup SPI at power-on and add 'ctrl' instruction to asm.py
#  DONE SPI: Expander control (Enable/disable slave, set bank etc)
#  DONE SPI: SYS Exchange bytes
#  DONE SYS: Reinitialize waveforms at soft reset, not just at power on
#  DONE v6502: Prototype. Retire bootCount to free up zp variables
#  DONE v6502: Allow soft reset when v6502 is active
#  DONE Apple1: As easter egg, preload with WozMon and Munching6502
#  DONE Apple1: Don't use buttonState but serialRaw
#  DONE Snake: Don't use serialRaw but buttonState
#  DONE Snake: Head-only snake shouldn't be allowed to turn around #52
#  DONE Snake: Improve game play and colors in general
#  DONE Snake: Tweak AI. Also autoplayer can't get hiscore anymore
#  DONE Racer: Don't use serialRaw but buttonState
#  DONE Racer: Faster road setup with SYS_SetMemory
#  DONE Makefile: Pass app-specific SYS functions on command line (.py files)
#  DONE Main: "Press [A] to start": accept keyboard also (incl. 'A') #38
#  DONE Add 4 arrows to font to fill up the ROM page
#  DONE Mode 1975 (for "zombie" mode), can do mode -1 to recover
#  DONE TinyBASIC: support larger font and MODE 1975. Fix indent issue #40
#  DONE Add channelMask to switch off the higher sound channels
#  DONE Loader: clear channelMask when loading into sound channels
#  DONE Update romTypeValue and interface.json
#  DONE Update version number to v4
#  DONE Formally Support SPI and RAM expander: publish in interface.json
#  DONE Use `inspect' to make program listing with original comments #127
#
#-----------------------------------------------------------------------
#
#  Ideas for ROM v5:
#
#  DONE v6502: Test with VTL02
#  DONE v6502: Test with Microchess
#  DONE Sound: Better noise by changing wavX every frame (at least in channel 1)
#  DONE Sound demo: Play SMB Underworld tune
#  DONE SPI: Also reset state at soft reset
#  DONE Fix clobbering of 0x81 by SPI SYS functions #103
#  DONE Control variable to black out the area at the top of the screen
#  DONE Fix possible video timing error in Loader #100
#  DONE Fix zero page usage in Bricks and Tetronis #41
#  DONE Add CALLI instruction to vCPU
#  DONE Add CMPHS/CMPHU instructions to vCPU XXX Still needs testing
#  DONE Main: add Apple1 to main menu
#  DONE Replace egg with something new
#  DONE Split interface.json and interface-dev.json
#  DONE MSBASIC
#  DONE Speed up SetMemory by 300% using bursts #126
#  DONE Discoverable ROM contents #46
#  DONE Vertical blank interrupt #125
#  DONE TinyBASIC: Support hexadecimal numbers $....
#  DONE Expander: Auto-detect banking, 64K and 128K (multiple tests)
#  DONE Cardboot: Boot from *.GT1 file if SDC/MMC detected
#  DONE CardBoot: Strip non-essentials
#  DONE CardBoot: Fix card type detection
#  DONE CardBoot: Read full sector
#  DONE Apple-1: Memory mapped PIA emulation using interrupt (D010-D013)
#  DONE Apple-1: Include A1 Integer BASIC
#  DONE Apple-1: Suppress lower case
#  DONE Apple-1: Include Mastermind and 15-Puzzle
#  DONE Apple-1: Include mini-assembler
#  DONE Apple-1: Intercept cassette interface = menu
#  XXX  Reduce the Pictures application ROM footprint #120
#  DONE Mandelbrot: Faster Mandelbrot using qwertyface's square trick
#  PART Main: Better startup chime, eg. sequence the 4 notes and then decay
#  XXX  Main: Some startup logo as intro, eg. gigatron letters from the box
#  DONE Racer: Control speed with up/down (better for TypeC controllers)
#  DONE Racer: Make noise when crashing
#  NO   Loader: make noise while loading (only channel 1 is safe to use)
#  DONE Faster SYS_Exec_88, with start address (GT1)?
#  DONE Let SYS_Exec_88 clear channelMask when loading into live channels
#  UNK  Investigate: Babelfish sometimes freezes during power-on?
#
#  Ideas for ROM v6+
#  XXX  ROM functions: SYS_PrintString, control codes, SYS_DrawChar, SYS_Newline
#  XXX  v8080 prepping for CP/M
#  XXX  vForth virtual CPU
#  XXX  Video: Increase vertical resolution with same videoTable (160 lines?)
#  XXX  Video mode for 12.5 MHz systems
#  XXX  Pucrunch (well documented) or eximozer 3.0.2 (better compression)
#  XXX  SPI: Think about SPI modes (polarities)
#  XXX  I2C: Turn SPI port 2-3 into a I2C port as suggesred by jwolfram
#  XXX  Reset.c and Main.c (that is: port these from GCL to C, but requires LCC fixed)
#  XXX  Need keymaps in ROM? (perhaps undocumented if not tested)
#  XXX  FrogStroll (not in Contrib/)
#  XXX  How it works memo: brief description of every software function
#  XXX  Adjustable return for LUP trampolines (in case SYS functions need it)
#  XXX  Loader: make noise when data comes in
#  XXX  vCPU: Multiplication (mulShift8?)
#  XXX  vCPU: Interrupts / Task switching (e.g for clock, LED sequencer)
#  XXX  Scroll out the top line of text, or generic vertical scroll SYS call
#  XXX  SYS function for plotting a full character in one go
#  XXX  Multitasking/threading/sleeping (start with date/time clock in GCL)
#-----------------------------------------------------------------------

import importlib
from sys import argv
from os  import getenv

from asm import *
import gcl0x as gcl
import font_v4 as font


# Enable patches for 512k board --
# Roms compiled with this option take full advantage
# of the 512k extension board but are only suitable
# for the Gigatron512k.
WITH_512K_BOARD = defined('WITH_512K_BOARD')

# Enable patches for 128k board --
# Roms compiled with this option can only be used
# with a Gigatron equipped with a 128k extension board.
# This patch forces the framebuffer to remain in banks 0
# or 1 regardless of the bank selected for the vCPU.
# This is never needed for the Gigatron512k because the hardware
# enforces this. This may not be needed for a Gigatron128k equipped
# with a suitable hardware patch.
WITH_128K_BOARD = defined('WITH_128K_BOARD')

# Variable WITH_SPI_BITS defines the number of potential MISO bits in
# bytes returned by a RAM&IO expansion board (in range 1 to 4). The
# GAL-based expansion boards work will all four settings. Marcel's
# original board theoretically offers four spi channels but in
# practice supports only one connected device on one of the first
# WITH_SPI_BITS channels. Hans61 7400-based board with two channels
# and Alastair's Gigasaur work best with WITH_SPI_BITS=2.

WITH_SPI_BITS = defined('WITH_SPI_BITS', 2)


# Rom name --
# This is the stem of the target rom name
# in case it differs from the source file stem
ROMNAME = defined('ROMNAME', argv[0])
if ROMNAME.endswith('.rom'):
  ROMNAME, _ = splitext(ROMNAME)
if ROMNAME.endswith('.py'):
  ROMNAME, _ = splitext(ROMNAME)
if ROMNAME.endswith('.asm'):
  ROMNAME, _ = splitext(ROMNAME)

# Displayed rom name --
# This is the name displayed by Reset.gcl.
# It defaults to '[DEV7]'
DISPLAYNAME = defined('DISPLAYNAME', "[DEV7]")


# Listing starts here
enableListing()
#-----------------------------------------------------------------------
#
#  Start of core
#
#-----------------------------------------------------------------------

# Pre-loading the formal interface as a way to get warnings when
# accidentally redefined with a different value
loadBindings('interface.json')
loadBindings('Core/interface-dev.json') # Provisional values for DEVROM

# Gigatron clock
cpuClock = 6.250e+06

# Output pin assignment for VGA
R, G, B, hSync, vSync = 1, 4, 16, 64, 128
syncBits = hSync+vSync # Both pulses negative

# When the XOUT register is in the circuit, the rising edge triggers its update.
# The loop can therefore not be agnostic to the horizontal pulse polarity.
assert syncBits & hSync != 0

# VGA 640x480 defaults (to be adjusted below!)
vFront = 10     # Vertical front porch
vPulse = 2      # Vertical sync pulse
vBack  = 33     # Vertical back porch
vgaLines = vFront + vPulse + vBack + 480
vgaClock = 25.175e+06

# Video adjustments for Gigatron
# 1. Our clock is (slightly) slower than 1/4th VGA clock. Not all monitors will
#    accept the decreased frame rate, so we restore the frame rate to above
#    minimum 59.94 Hz by cutting some lines from the vertical front porch.
vFrontAdjust = vgaLines - int(4 * cpuClock / vgaClock * vgaLines)
vFront -= vFrontAdjust
# 2. Extend vertical sync pulse so we can feed the game controller the same
#    signal. This is needed for controllers based on the 4021 instead of 74165
vPulseExtension = max(0, 8-vPulse)
vPulse += vPulseExtension
# 3. Borrow these lines from the back porch so the refresh rate remains
#    unaffected
vBack -= vPulseExtension

# Start value of vertical blank counter
videoYline0 = 1-2*(vFront+vPulse+vBack-2)

# Mismatch between video lines and sound channels
soundDiscontinuity = (vFront+vPulse+vBack) % 4

# QQVGA resolution
qqVgaWidth      = 160
qqVgaHeight     = 120

# Game controller bits (actual controllers in kit have negative output)
# +----------------------------------------+
# |       Up                        B*     |
# |  Left    Right               B     A*  |
# |      Down      Select Start     A      |
# +----------------------------------------+ *=Auto fire
buttonRight     = 1
buttonLeft      = 2
buttonDown      = 4
buttonUp        = 8
buttonStart     = 16
buttonSelect    = 32
buttonB         = 64
buttonA         = 128

#-----------------------------------------------------------------------
#
#  RAM page 0: zero-page variables
#
#-----------------------------------------------------------------------

# Memory size in pages from auto-detect
memSize         = zpByte()

# The current channel number for sound generation. Advanced every scan line
# and independent of the vertical refresh to maintain constant oscillation.
channel         = zpByte()

# Next sound sample being synthesized
sample          = zpByte()
# To save one instruction in the critical inner loop, `sample' is always
# reset with its own address instead of, for example, the value 0. Compare:
# 1 instruction reset
#       st sample,[sample]
# 2 instruction reset:
#       ld 0
#       st [sample]
# The difference is not audible. This is fine when the reset/address
# value is low and doesn't overflow with 4 channels added to it.
# There is an alternative, but it requires pull-down diodes on the data bus:
#       st [sample],[sample]
assert 4*63 + sample < 256
# We pin this reset/address value to 3, so `sample' swings from 3 to 255
assert sample == 3

# Former bootCount and bootCheck (<= ROMv3)
zpReserved      = zpByte() # Recycled and still unused. Candidate future uses:
                           # - Video driver high address (for alternative video modes)
                           # - v6502: ADH offset ("MMU")
                           # - v8080: ???
vCpuSelect      = zpByte() # Active interpreter page

if WITH_128K_BOARD:
  entropy      = zpByte(2) # Entropy harvested from SRAM startup and controller input
  ctrlVideo    = zpByte()  # ctrl bits for video access
else:
  entropy      = zpByte(3) # Entropy harvested from SRAM startup and controller input

# Visible video
videoY          = zpByte() # Counts up from 0 to 238 in steps of 2
                           # Counts up (and is odd) during vertical blank
videoModeB      = zpByte() # Handler for every 2nd line (pixel burst or vCPU)
videoModeC      = zpByte() # Handler for every 3rd line (pixel burst or vCPU)
videoModeD      = zpByte() # Handler for every 4th line (pixel burst or vCPU)

nextVideo       = zpByte() # Jump offset to scan line handler (videoA, B, C...)
videoPulse      = nextVideo # Used for pulse width modulation

# Frame counter is good enough as system clock
frameCount      = zpByte(1)

# Serial input (game controller)
serialRaw       = zpByte() # New raw serial read
serialLast      = zpByte() # Previous serial read
buttonState     = zpByte() # Clearable button state
resetTimer      = zpByte() # After 2 seconds of holding 'Start', do a soft reset
                           # XXX move to page 1 to free up space

# Extended output (blinkenlights in bit 0:3 and audio in bit 4:7). This
# value must be present in AC during a rising hSync edge. It then gets
# copied to the XOUT register by the hardware. The XOUT register is only
# accessible in this indirect manner because it isn't part of the core
# CPU architecture.
xout            = zpByte()
xoutMask        = zpByte() # The blinkenlights and sound on/off state

# vCPU interpreter
vTicks          = zpByte()  # Interpreter ticks are units of 2 clocks
vPC             = zpByte(2) # Interpreter program counter, points into RAM
vAC             = zpByte(2) # Interpreter accumulator, 16-bits
vLR             = zpByte(2) # Return address, for returning after CALL
vSP             = zpByte(2) # Stack pointer (16 bits!)
vReturn         = zpByte()  # Return into video loop (in page of vBlankStart)

# Scratch
frameX          = zpByte() # Starting byte within page
frameY          = zpByte() # Page of current pixel line (updated by videoA)

# Vertical blank (reuse some variables used in the visible part)
videoSync0      = frameX   # Vertical sync type on current line (0xc0 or 0x40)
videoSync1      = frameY   # Same during horizontal pulse (0x80 or 0x00)

# Versioning for GT1 compatibility
# Please refer to Docs/GT1-files.txt for interpreting this variable
romType         = zpByte(1)

# The low 3 bits are repurposed to select the actively updated sound channels.
# Valid bit combinations are:
#  xxxxx011     Default after reset: 4 channels (page 1,2,3,4)
#  xxxxx001     2 channels at double update rate (page 1,2)
#  xxxxx000     1 channel at quadruple update rate (page 1)
# The main application for this is to free up the high bytes of page 2,3,4.
channelMask = symbol('channelMask_v4')
assert romType == channelMask

# SYS function arguments and results/scratch
sysFn           = zpByte(2)
sysArgs         = zpByte(8)
fsmState        = sysArgs+7

# Play sound if non-zero, count down and stop sound when zero
soundTimer      = zpByte()

# Former ledTimer
if WITH_128K_BOARD:
  ctrlCopy      = zpByte() # ctrl bits for vcpu access
else:
  zpReserved2   = zpByte()

# LED state machine
ledState_v2     = zpByte() # Current LED state

# Former ledTempo
vTmp            = zpByte() # Scratch byte

# Management of free space in page zero (userVars)
# * Programs that only use the features of ROMvx can
#   safely use all bytes above userVars_vx except 0x80.
# * Programs that use some but not all features of ROMvx
#   may exceptionally use bytes between userVars
#   and userVars_vx if they avoid using ROM features
#   that need them. This is considerably riskier.
userVars        = zpByte(0)

# Start of safely usable bytes under ROMv4
userVars_v4     = zpByte(0)
vIrqSave        = zpByte(6) # saved vcpu context during virq
# Start of safely usable bytes under ROMv5,6,7
userVars_v5     = zpByte(0)
userVars_v6     = zpByte(0)
userVars_v7     = zpByte(0)

# [0x80] Constant 0x01
oneConst        = 0x80

zpReset(0x81)                 # Second variable zone
userVars2       = zpByte(0)
userVars2_v4    = zpByte(0)+1 # ROMv4's ctrlBits at 0x81!!!
userVars2_v5    = zpByte(0)
userVars2_v6    = zpByte(0)
vFAS            = zpByte(1)   # FAC sign
vFAE            = zpByte(1)   # FAC exponent
vLAX            = zpByte(1)   # Extended long accumulator (40 bits)
vLAC            = zpByte(4)   # Long accumulator (32 bits)
vT2             = zpByte(2)   # T2 register
vT3             = zpByte(2)   # T3 register
userVars2_v7    = zpByte(0)


#-----------------------------------------------------------------------
#
#  RAM page 1: video line table
#
#-----------------------------------------------------------------------

# Byte 0-239 define the video lines
videoTable      = 0x0100 # Indirection table: Y[0] dX[0]  ..., Y[119] dX[119]

vReset          = 0x01f0 # Reset stub
if WITH_128K_BOARD:
  entropy2      = 0x01f2 # (displaced) Entropy hidden state
ledTempo        = 0x01f3 # (displaced) Led timer reset value
ledTimer        = 0x01f4 # (displaced) Ticks until next LED change
vIrqCtx_v7      = 0x01f5 # context page for irq
vIRQ_v5         = 0x01f6 # vIRQ vector
ctrlBits        = 0x01f8 # Expansion control bits
videoTop_v5     = 0x01f9 # Number of skipped lines

# Highest bytes are for sound channel variables
wavA = 250      # Waveform modulation with `adda'
wavX = 251      # Waveform modulation with `xora'
keyL = 252      # Frequency low 7 bits (bit7 == 0)
keyH = 253      # Frequency high 8 bits
oscL = 254      # Phase low 7 bits
oscH = 255      # Phase high 8 bits

#-----------------------------------------------------------------------
#  Memory layout
#-----------------------------------------------------------------------

userCode = 0x0200       # Application vCPU code
soundTable = 0x0700     # Wave form tables (doubles as right-shift-2 table)
screenMemory = 0x0800   # Default start of screen memory: 0x0800 to 0x7fff

#-----------------------------------------------------------------------
#  Application definitions
#-----------------------------------------------------------------------

maxTicks = 30//2                # Duration of vCPU's slowest virtual opcode (ticks)
minTicks = 14//2                # vcPU's fastest instruction
v6502_maxTicks = 38//2          # Max duration of v6502 processing phase (ticks)

runVcpu_overhead = 5            # Caller overhead (cycles)
vCPU_overhead = 9               # Callee overhead of jumping in and out (cycles)
v6502_overhead = 11             # Callee overhead for v6502 (cycles)

v6502_adjust = (v6502_maxTicks - maxTicks) + (v6502_overhead - vCPU_overhead)//2
assert v6502_adjust >= 0        # v6502's overhead is a bit more than vCPU


def runVcpu_ticks(n, overhead, ref=None):
  overhead += vCPU_overhead
  n -= overhead
  assert n > 0
  m = n % 2                     # Need alignment?
  n //= 2
  n -= maxTicks                 # First instruction always runs
  assert n < 128
  assert n >= v6502_adjust
  print('runVcpu at $%04x net cycles %3s info %s' % (pc(), (n + maxTicks) * 2, ref))
  return n, m

def runVcpu(n, ref=None, returnTo=None):
  """Macro to run interpreter for exactly n cycles. Returns 0 in AC.

  - `n' is the number of available Gigatron cycles including overhead.
    This is converted into interpreter ticks and takes into account
    the vCPU calling overheads. A `nop' is inserted when necessary
    for alignment between cycles and ticks.
  - `returnTo' is where program flow continues after return. If not set
     explicitely, it will be the first instruction behind the expansion.
  - If another interpreter than vCPU is active (v6502...), that one
    must adjust for the timing differences, because runVcpu wouldn't know."""

  overhead = runVcpu_overhead
  if returnTo == 0x100:         # Special case for videoZ
    overhead -= 2

  if n is None:
    # (Clumsily) create a maximum time slice, corresponding to a vTicks
    # value of 127 (giving 282 cycles). A higher value doesn't work because
    # then SYS functions that just need 28 cycles (0 excess) won't start.
    n = (127 + maxTicks) * 2 + overhead + vCPU_overhead

  n, m = runVcpu_ticks(n, overhead, ref)

  ld([vCpuSelect],Y)            #0 Allows us to use ctrl() just before runVcpu
  if m == 1:
      st(0,[0])                 # Tick alignment
  if returnTo != 0x100:
    if returnTo is None:
      returnTo = pc() + 4       # Next instruction
    ld(lo(returnTo))            #1
    st([vReturn])               #2
  jmp(Y,'ENTER')                #3
  ld(n)                         #4
assert runVcpu_overhead ==       5


#-----------------------------------------------------------------------
#       v6502 definitions
#-----------------------------------------------------------------------

# Registers are zero page variables
v6502_PC        = vLR           # Program Counter
v6502_PCL       = vLR+0         # Program Counter Low
v6502_PCH       = vLR+1         # Program Counter High
v6502_S         = vSP           # Stack Pointer (kept as "S+1")
v6502_A         = vAC+0         # Accumulator
v6502_BI        = vAC+1         # B Input Register (used by SBC)
v6502_ADL       = sysArgs+0     # Low Address Register
v6502_ADH       = sysArgs+1     # High Address Register
v6502_IR        = sysArgs+2     # Instruction Register
v6502_P         = sysArgs+3     # Processor Status Register (V flag in bit 7)
v6502_Qz        = sysArgs+4     # Quick Status Register for Z flag
v6502_Qn        = sysArgs+5     # Quick Status Register for N flag
v6502_X         = sysArgs+6     # Index Register X
v6502_Y         = sysArgs+7     # Index Register Y
v6502_Tmp       = vTmp          # Scratch (may be clobbered outside v6502)

# MOS 6502 definitions for P register
v6502_Cflag = 1                 # Carry Flag (unsigned overflow)
v6502_Zflag = 2                 # Zero Flag (all bits zero)
v6502_Iflag = 4                 # Interrupt Enable Flag (1=Disable)
v6502_Dflag = 8                 # Decimal Enable Flag (aka BCD mode, 1=Enable)
v6502_Bflag = 16                # Break (or PHP) Instruction Flag
v6502_Uflag = 32                # Unused (always 1)
v6502_Vflag = 64                # Overflow Flag (signed overflow)
v6502_Nflag = 128               # Negative Flag (bit 7 of result)

# In emulation it is much faster to keep the V flag in bit 7
# This can be corrected when importing/exporting with PHP, PLP, etc
v6502_Vemu = 128

# On overflow:
#       """Overflow is set if two inputs with the same sign produce
#          a result with a different sign. Otherwise it is clear."""
# Formula (without carry/borrow in!):
#       (A ^ (A+B)) & (B ^ (A+B)) & 0x80
# References:
#       http://www.righto.com/2012/12/the-6502-overflow-flag-explained.html
#       http://6502.org/tutorials/vflag.html

# Memory layout
v6502_Stack     = 0x0000        # 0x0100 is already used in the Gigatron
#v6502_NMI      = 0xfffa
#v6502_RESET    = 0xfffc
#v6502_IRQ      = 0xfffe

#-----------------------------------------------------------------------
#
#  $0000 ROM page 0: Boot
#
#-----------------------------------------------------------------------

align(0x100, size=0x80)

# Give a first sign of life that can be checked with a voltmeter
ld(0b0000)                      # LEDs |OOOO|
ld(syncBits^hSync,OUT)          # Prepare XOUT update, hSync goes down, RGB to black
ld(syncBits,OUT)                # hSync goes up, updating XOUT

# Setup I/O and RAM expander
ctrl(0b01111111)                # Reset signal (default state | 0x3)
ctrl(0b01111100)                # Disable SPI slaves, enable RAM, bank 1
#      ^^^^^^^^
#      |||||||`-- SCLK
#      ||||||`--- Not connected
#      |||||`---- /SS0
#      ||||`----- /SS1
#      |||`------ /SS2
#      ||`------- /SS3
#      |`-------- B0
#      `--------- B1
# bit15 --------- MOSI = 0

# Simple RAM test and size check by writing to [1<<n] and see if [0] changes or not.
ld(1)                           # Quick RAM test and count
label('.countMem0')
st([memSize],Y)                 # Store in RAM and load AC in Y
ld(255)
xora([Y,0])                     # Invert value from memory
st([Y,0])                       # Test RAM by writing the new value
st([0])                         # Copy result in [0]
xora([Y,0])                     # Read back and compare if written ok
bne(pc())                       # Loop forever on RAM failure here
ld(255)
xora([Y,0])                     # Invert memory value again
st([Y,0])                       # To restore original value
xora([0])                       # Compare with inverted copy
beq('.countMem1')               # If equal, we wrapped around
ld([memSize])
bra('.countMem0')               # Loop to test next address line
adda(AC)                        # Executes in the branch delay slot!
label('.countMem1')

# Momentarily wait to allow for debouncing of the reset switch by spinning
# roughly 2^15 times at 2 clocks per loop: 6.5ms@10MHz to 10ms@6.3MHz
# Real-world switches normally bounce shorter than that.
# "[...] 16 switches exhibited an average 1557 usec of bouncing, with,
#  as I said, a max of 6200 usec" (From: http://www.ganssle.com/debouncing.htm)
# Relevant for the breadboard version, as the kit doesn't have a reset switch.

ld(255)                         # Debounce reset button
label('.debounce')
st([0])
bne(pc())
suba(1)                         # Branch delay slot
ld([0])
bne('.debounce')
suba(1)                         # Branch delay slot

# Update LEDs (memory is present and counted, reset is stable)
ld(0b0001)                      # LEDs |*OOO|
ld(syncBits^hSync,OUT)
ld(syncBits,OUT)

# Scan the entire RAM space to collect entropy for a random number generator.
# The 16-bit address space is scanned, even if less RAM was detected.
ld(0)                           # Collect entropy from RAM
st([vAC+0],X)
st([vAC+1],Y)
label('.initEnt0')
ld([entropy+0])
bpl('.initEnt1')
adda([Y,X])
xora(191)
label('.initEnt1')
st([entropy+0])
ld([entropy+1])
bpl('.initEnt2')
adda([entropy+0])
xora(193)
label('.initEnt2')
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
bne('.initEnt0')
st([vAC+0],X)
ld([vAC+1])
adda(1)
bne('.initEnt0')
st([vAC+1],Y)

# Update LEDs
ld(0b0011)                      # LEDs |**OO|
ld(syncBits^hSync,OUT)
ld(syncBits,OUT)

# vCPU reset handler
ld(hi('ENTER'))                 # vCPU is the active interpreter
st([vCpuSelect])
ld((vReset&255)-2)              # Setup reset handler
st([vPC])
adda(2,X)
ld(vReset>>8)
st([vPC+1],Y)
st(lo('PREFIX35'),    [Y,Xpp])  # vReset
st(lo('RESET_v7'),    [Y,Xpp])

# Init key variables (Y=1)
ld(0)
st([0])                         # Carry lookup ([0x80] in 1st line of vBlank)
st([channel])
st([soundTimer])
st([Y, vIrqCtx_v7])
st([Y, vIRQ_v5])
st([Y, vIRQ_v5+1])
st([Y, videoTop_v5])
ld(255)                         # Setup serial input
st([frameCount])
st([serialRaw])
st([serialLast])
st([buttonState])
st([resetTimer])                # resetTimer<0 when entering Main.gcl
ld(0x7c)
st([Y, ctrlBits])
st([ctrlVideo]) if WITH_128K_BOARD else nop()
st([ctrlCopy])  if WITH_128K_BOARD else nop()

ld(0b1111)                      # LEDs |****|
ld(syncBits^hSync,OUT)
ld(syncBits,OUT)
st([xout])                      # Setup for control by video loop
st([xoutMask])

# Start
ld(hi('startVideo'),Y)          # Enter video loop at vertical blank
jmp(Y,'startVideo')
st([ledState_v2])               # Setting to 1..126 means "stopped"

#-----------------------------------------------------------------------
# Soft reset
#-----------------------------------------------------------------------

# Resets the gigatron without breaking the video loop.
# This mostly consists of executing Reset.gt1.
#
# This used to be achieved with a SYS_Reset_88 that was removed
# from interface.json for ROMv5a in order to prefer achieving this
# by jumping to vReset. Instead of a SYS call, this is now
# achieved by a secret vCPU instruction RESET_v7 that frees
# the [1f2-1f5] space for other purposes.

# ROM type (see also Docs/GT1-files.txt)
romTypeValue = symbol('romTypeValue_DEVROM')

label('softReset#24')
ld(0)                           #24
st([vSP])                       #25 vSP
st([vSP+1])                     #26
ld(hi('videoTop_v5'),Y)         #27
st([Y,lo('videoTop_v5')])       #28 Show all 120 pixel lines
st([Y,vIrqCtx_v7])              #29
st([Y,vIRQ_v5])                 #30 Disable vIRQ dispatch
st([Y,vIRQ_v5+1])               #31
st([soundTimer])                #32 soundTimer
st([vLR])                       #33 vLR
st([vLR+1])                     #34
st([videoModeC]) if WITH_512K_BOARD else None
ld(0x7c)                        #35/36
st([Y,ctrlBits])                #36/37
st([ctrlVideo])  if WITH_128K_BOARD else nop()
st([ctrlCopy])   if WITH_128K_BOARD else nop()
ld('nopixels')                  #39/40
st([videoModeC]) if not WITH_512K_BOARD else None
st([videoModeB])                #41
st([videoModeD])                #42
# Set romTypeValue
assert (romTypeValue & 7) == 0
ld(romTypeValue)                #43 Set ROM type/version and clear channel mask
st([romType])                   #44
# Reset expansion board
ctrl(0b01111111)                #45 Reset signal (default state | 0x3)
ctrl(0b01111100)                #46 Default state.
# Adjust ticks
ld([vTicks])                    #47 Always load after ctrl
adda(-38/2)                     #48-38=10
st([vTicks])                    #11
ld('Reset')                     #12 Reset.gt1 from EPROM
st([sysArgs+0])                 #13
ld(hi('Reset'))                 #14
ld(hi('sys_Exec'),Y)            #15
jmp(Y,'sys_Exec')               #16
st([sysArgs+1])                 #17



#-----------------------------------------------------------------------
# Placeholders for future SYS functions. This works as a kind of jump
# table. The indirection allows SYS implementations to be moved around
# between ROM versions, at the expense of 2 clock cycles (or 1). When
# the function is not present it just acts as a NOP. Of course, when a
# SYS function must be patched or extended it needs to have budget for
# that in its declared maximum cycle count.
#
# Technically the same goal can be achieved by starting each function
# with 2 nop's, or by overdeclaring their duration in the first place
# (a bit is still wise to do). But this can result in fragmentation
# of future ROM images. The indirection avoids that.
#
# An added advantage of having these in ROM page 0 is that it saves one
# byte when setting sysFn: LDI+STW (4 bytes) instead of LDWI+STW (5 bytes)
#-----------------------------------------------------------------------

align(0x80, size=0x80)
assert pc() == 0x80

ld(hi('REENTER'),Y)             #15 slot 0x80
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x83
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x86
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x89
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x8c
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x8f
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x92
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x95
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x98
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0x9b
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

#-----------------------------------------------------------------------
# Extension SYS_Multiply_s16_v6_66: 16 bit multiplication
# Also known as SYS_Multiply_s16_v7_34.
#-----------------------------------------------------------------------
#
# Computes C = C + A * B where A,B,C are 16 bits integers.
# Returns product in vAC as well
#
#       sysArgs[0:1]    Multiplicand A (in)
#       sysArgs[2:3]    Multiplicand B (in)
#       sysArgs[4:5]    C (inout)
#       sysArgs[6:7]    (changed)
#
# Original design: at67
#
# The improved dev7rom version is substantially faster.
# Alternatively use the new opcode MULW.

label('SYS_Multiply_s16_v6_66')
label('SYS_Multiply_s16_v7_34')
ld(hi('sys_Multiply_s16'),Y)    #15 slot 0x9e
jmp(Y,'sys_Multiply_s16')       #16
nop()

#-----------------------------------------------------------------------
# Extension SYS_Divide_s16_v6_80: 15 bit division
# Also known as SYS_Divide_u16_v7_34
#-----------------------------------------------------------------------
#
# Computes the Euclidean division of 0<=A<65536 and 0<B<65536.
# The s16 component of the name is a misnomer (should be u15).
# For 16 bits signed division, additional code must handle the signs
# Return the quotient in vAC as well as sysArgs[01]
# Return the remainder in sysArgs[45]
#
#       sysArgs[0:1]    Dividend A (in) Quotient (out)
#       sysArgs[2:3]    Divisor B (in)
#       sysArgs[4:5]    Remainder (out)
#       sysArgs[6:7]    (changed)
#
# Original design by at67.
#
# The improced dev7rom version handles unrestricted 16 bits unsigned division
# that is 0 <= A,B <= 65535. An external wrapper is still needed for signed
# division. Alternatively any of the new opcodes RDIVU or RDIVS.

label('SYS_Divide_s16_v6_80')
label('SYS_Divide_u16_v7_34')
ld(hi('sys_Divide_u16'),Y)      #15 slot 0xa1
jmp(Y,'sys_Divide_u16')         #16
nop()

#-----------------------------------------------------------------------
# More placeholders for future SYS functions
#-----------------------------------------------------------------------

ld(hi('REENTER'),Y)             #15 slot 0xa4
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xa7
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xaa
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

#-----------------------------------------------------------------------
# Extension SYS_Exec_88: Load code from ROM into memory and execute it
#-----------------------------------------------------------------------
#
# This loads the vCPU code with consideration of the current vSP
# Used during reset, but also for switching between applications or for
# loading data from ROM from within an application (overlays).
#
# ROM stream format is
#  [<addrH> <addrL> <n&255> n*<byte>]* 0 [<execH> <execL>]
# on top of lookup tables.
#
#       sysArgs[0:1]    ROM pointer (in)
#       sysArgs[2:3]    RAM pointer (changed) Execution address (out)
#       sysArgs[4]      Byte counter (changed)
#       sysArgs[7]      FSM state (changed)
#       vLR==0          vCPU continues at GT1 execution address (in)
#       vLR!=0          vCPU continues at vLR (in)

label('SYS_Exec_88')
ld(hi('sys_Exec'),Y)            #15
jmp(Y,'sys_Exec')               #16
nop()                           #17

#-----------------------------------------------------------------------
# Extension SYS_Loader_DEVROM_44: Load code from serial input and execute
#-----------------------------------------------------------------------
#
# This loads vCPU code and data presented on the serial port according
# to the loader protocol then jumps to the avertised execution
# address. This call never returns.
#
# Set sysArgs[0] to 0xc to enable visual feedback in the pixel
# row located in page sysArgs[1]. This is automatically
# disabled if bytes are loaded in the feedback area.
#
#       sysArgs[0]      Zero to disable echo (0x00 or ox0c) (in)
#       sysArgs[1]      Echo row (0x59) (in)
#
# Credits: The first native loader was written for ROMvX0 by at67.
#
# Loader protocol
# ---------------
# The data is divided into chunks of at most 60 bytes to be loaded at
# contiguous addresses inside a same gigatron memory page. Each chunk
# is transmitted over the serial port (IN) synchronously with the
# video signal, one chunk per frame. Each byte of the chunk must be
# read from the IN port when videoY takes specific values:
#
#  videoY    Data
#   207      protocol signature: 'L'
#   219      chunk length (low 6 bits) or zero to execute.
#   235      chunk address (l) or execution address (l) if len=0
#   251      chunk address (h) or execution address (h)  if len=0
#   2        chunk byte 0
#   6        chunk byte 1
#  ....
#   2+4*k    chunk byte k

ld(hi('sys_Loader'),Y)          #15 slot 0xb0
jmp(Y,'sys_Loader')             #16
ld([sysArgs+0])                 #17

#-----------------------------------------------------------------------
# More placeholders for future SYS functions
#-----------------------------------------------------------------------

ld(hi('REENTER'),Y)             #15 slot 0xb3
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xb6
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xb9
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xbc
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xbf
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xc2
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xc5
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xc8
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xcb
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xce
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xd1
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xd4
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xd7
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xda
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

ld(hi('REENTER'),Y)             #15 slot 0xdd
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17


#-----------------------------------------------------------------------
# Extension SYS_DoubleDabble_v7_34
#-----------------------------------------------------------------------

# SYS function to help converting integers into ascii in any base.
# The string of bytes [sysArgs[2:3]...sysArgs[0:1]-1] represents
# a number in base sysArgs[4]. Calling the SYS function doubles
# this number and adds 1 if vAC<=0 (msb set). If necessary
# sysArgs[2:3] is decremented to make space for a new digit.
#
# sysArgs[0:1]       (in)    End address
# sysArgs[2:3]       (inout) Start address
# sysArgs[4]         (in)    Base
# vAC                (in)    Carry in high bit
# sysArgs[5]         (used)

label('SYS_DoubleDabble_v7_34')
ld(hi('sys_DoubleDabble'),Y)    #15 slot 0xe0
jmp(Y,'sys_DoubleDabble')       #16
ld([vAC+1])                     #17


#-----------------------------------------------------------------------
# Extension SYS_ScanMemoryExt_v6_50
#-----------------------------------------------------------------------

# SYS function for searching a byte in a 0 to 256 bytes string located
# in a different bank. Doesn't cross page boundaries. Returns a
# pointer to the target if found or zero. Temporarily deselects SPI
# devices.
#
# sysArgs[0:1]            Start address
# sysArgs[2], sysArgs[3]  Bytes to locate in the string
# vACL                    Length of the string (0 means 256)
# vACH                    Bit 6 and 7 contain the bank number

label('SYS_ScanMemoryExt_v6_50')
ld(hi('sys_ScanMemoryExt'),Y)   #15 slot 0xe3
jmp(Y,'sys_ScanMemoryExt')      #16
ld([vAC+1])                     #17


#-----------------------------------------------------------------------
# Extension SYS_ScanMemory_v6_50
#-----------------------------------------------------------------------

# SYS function for searching a byte in a 0 to 256 bytes string.
# Returns a pointer to the target if found or zero.  Doesn't cross
# page boundaries.
#
# sysArgs[0:1]            Start address
# sysArgs[2], sysArgs[3]  Bytes to locate in the string
# vACL                    Length of the string (0 means 256)

label('SYS_ScanMemory_v6_50')
ld(hi('sys_ScanMemory'),Y)      #15 slot 0xe6
jmp(Y,'sys_ScanMemory')         #16
ld([sysArgs+1],Y)               #17

#-----------------------------------------------------------------------
# Extension SYS_CopyMemory_v6_80
#-----------------------------------------------------------------------

# SYS function for copying 1..256 bytes
#
# sysArgs[0:1]    Destination address
# sysArgs[2:3]    Source address
# vAC[0]          Count (0 means 256)
#
# Doesn't cross page boundaries.
# Overwrites sysArgs[4:7] and vLR.

label('SYS_CopyMemory_v6_80')
ld(hi('sys_CopyMemory'),Y)       # 15 slot 0xe9
jmp(Y, 'sys_CopyMemory')         # 16
ld([vAC])                        # 17

#-----------------------------------------------------------------------
# Extension SYS_CopyMemoryExt_v6_100
#-----------------------------------------------------------------------

# SYS function for copying 1..256 bytes across banks
#
# sysArgs[0:1]  Destination address
# sysArgs[2:3]  Source address
# vAC[0]        Count (0 means 256)
# vAC[1]        Bits 7 and 6 contain the destination bank number,
#               and bits 5 and 4 the source bank number.
#
# Doesn't cross page boundaries.
# Overwrites sysArgs[4:7], vLR, and vTmp.
# Temporarily deselect all SPI devices.
# Should not call without expansion board

label('SYS_CopyMemoryExt_v6_100')
ld(hi('sys_CopyMemoryExt'),Y)    # 15 slot 0xec
jmp(Y, 'sys_CopyMemoryExt')      # 16
ld([vAC+1])                      # 17

#-----------------------------------------------------------------------
# Extension SYS_ReadRomDir_v5_80
#-----------------------------------------------------------------------

# Get next entry from ROM file system. Use vAC=0 to get the first entry.

# Variables:
#       vAC             Start address of current entry (inout)
#       sysArgs[0:7]    File name, padded with zeroes (out)

label('SYS_ReadRomDir_v5_80')
ld(hi('sys_ReadRomDir'),Y)      #15
jmp(Y,'sys_ReadRomDir')         #16
ld([vAC+1])                     #17

#-----------------------------------------------------------------------
# Extension SYS_Out_22
#-----------------------------------------------------------------------

# Send byte to output port
# Variables:
#       vAC

fillers(until=0xf4)

label('SYS_Out_22')
ld([sysArgs+0],OUT)             #15
nop()                           #16
ld(hi('REENTER'),Y)             #17
jmp(Y,'REENTER')                #18
ld(-22/2)                       #19

#-----------------------------------------------------------------------
# Extension SYS_In_24
#-----------------------------------------------------------------------

# Read a byte from the input port
# Variables:
#       vAC

label('SYS_In_24')
st(IN, [vAC])                   #15
ld(0)                           #16
st([vAC+1])                     #17
nop()                           #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24/2)                       #21

assert pc()&255 == 0

#-----------------------------------------------------------------------
#
#  $0100 ROM page 1: Video loop vertical blank
#
#-----------------------------------------------------------------------
align(0x100, size=0x100)

# Video off mode (also no sound, serial, timer, blinkenlights, ...).
# For benchmarking purposes. This still has the overhead for the vTicks
# administration, time slice granularity etc.
label('videoZ')
videoZ = pc()
runVcpu(None, '---- novideo', returnTo=videoZ)

label('startVideo')             # (Re)start of video signal from idle state
ld(syncBits)

# Start of vertical blank interval
label('vBlankStart')
st([videoSync0])                #32 Start of vertical blank interval
ld(syncBits^hSync)              #33
st([videoSync1])                #34

# Reset line counter before vCPU can see it
ld(videoYline0)                 #35
st([videoY])                    #36

# Update frame count and [0x80] (4 cycles)
ld(1)                           #37 Reinitialize carry lookup, for robustness
st([0x80],Y)                    #38 And set Y=1 for 1fx variables
adda([frameCount])              #39 Frame counter
st([frameCount])                #40

# Mix entropy (11 cycles)
xora([entropy+1])               #41 Mix entropy
xora([serialRaw])               #42 Mix in serial input
adda([entropy+0])               #43
st([entropy+0])                 #44
if WITH_128K_BOARD:
  adda([Y,entropy2])            #45 Some hidden state
  st([Y,entropy2])              #46 (displaced third entropy byte)
else:
  adda([entropy+2])             #45 Some hidden state
  st([entropy+2])               #46 (preserved third entropy byte)
bmi(pc()+3)                     #47
bra(pc()+3)                     #48
xora(64+16+2+1)                 #49
xora(64+32+8+4)                 #49(!)
adda([entropy+1])               #50
st([entropy+1])                 #51

# LED sequencer (15 cycles)
ld([Y,ledTimer])                #52 Blinkenlight sequencer
suba(1)                         #53
bne('.leds#56')                 #54
st([Y,ledTimer])                #55
ld(1)                           #56
adda([ledState_v2])             #57
label('.leds#58')
bne(pc()+3)                     #58
bra(pc()+3)                     #59
ld(-24)                         #60 State 0 becomes -24, start of sequence
bgt('.leds#62')                 #60(!) Catch the stopped state (>0)
st([ledState_v2])               #61
adda('.leds#65')                #62
bra(AC)                         #63 Jump to lookup table
bra('.leds#66')                 #64 Single-instruction subroutine
label('.leds#56')
bge('.leds#58')                 #56
ld([ledState_v2])               #57
ld([Y,ledTempo])                #58
st([Y,ledTimer])                #59
bra(pc()+1)                     #60
nop()                           #61,62
bra('.leds#65')                 #63
ld([xoutMask])                  #64
label('.leds#62')
ld(0xf)                         #62 Maintain stopped state
st([ledState_v2])               #63
bra('.leds#66')                 #64
anda([xoutMask])                #65
ld(0b1111)                      #65 LEDs |****| offset -24 Low 4 bits are the LED output
ld(0b0111)                      #65 LEDs |***O|
ld(0b0011)                      #65 LEDs |**OO|
ld(0b0001)                      #65 LEDs |*OOO|
ld(0b0010)                      #65 LEDs |O*OO|
ld(0b0100)                      #65 LEDs |OO*O|
ld(0b1000)                      #65 LEDs |OOO*|
ld(0b0100)                      #65 LEDs |OO*O|
ld(0b0010)                      #65 LEDs |O*OO|
ld(0b0001)                      #65 LEDs |*OOO|
ld(0b0011)                      #65 LEDs |**OO|
ld(0b0111)                      #65 LEDs |***O|
ld(0b1111)                      #65 LEDs |****|
ld(0b1110)                      #65 LEDs |O***|
ld(0b1100)                      #65 LEDs |OO**|
ld(0b1000)                      #65 LEDs |OOO*|
ld(0b0100)                      #65 LEDs |OO*O|
ld(0b0010)                      #65 LEDs |O*OO|
ld(0b0001)                      #65 LEDs |*OOO|
ld(0b0010)                      #65 LEDs |O*OO|
ld(0b0100)                      #65 LEDs |OO*O|
ld(0b1000)                      #65 LEDs |OOO*|
ld(0b1100)                      #65 LEDs |OO**|
ld(0b1110)                      #65 LEDs |O***| offset -1
label('.leds#65')
anda(0xf)                       #65 Always clear sound bits
label('.leds#66')
st([xoutMask])                  #66 Sound bits will be re-enabled below

# Default video pulse length
ld(vPulse*2)                    #67 vPulse default length when not modulated
st([videoPulse])                #68

# When the total number of scan lines per frame is not an exact multiple of the
# (4) channels, there will be an audible discontinuity if no measure is taken.
# This static noise can be suppressed by swallowing the first `lines mod 4'
# partial samples after transitioning into vertical blank. This is easiest if
# the modulo is 0 (do nothing), 1 (reset sample when entering the last visible
# scan line), or 2 (reset sample while in the first blank scan line). For the
# last case there is no solution yet: give a warning.
extra = 0
if soundDiscontinuity == 2:
  st(sample, [sample])          # Sound continuity
  extra += 1
if soundDiscontinuity > 2:
  highlight('Warning: sound discontinuity not suppressed')

if WITH_128K_BOARD:
  # The cpu bank is enabled during vblank.
  # Rebuild ctrlBits{Video,Copy} since Y=1
  # at the cost of 7 extra cycles.
  ld([Y,ctrlBits])              #+1
  st([ctrlCopy],X)              #+2
  ctrl(X)                       #+3
  xora([ctrlVideo])             #+4 load after ctrl!
  anda(0x3c)                    #+5
  xora([ctrlVideo])             #+6
  st([ctrlVideo])               #+7
  extra += 7

# vCPU interrupt
ld([frameCount])                #69
beq('vBlankFirst#72')           #70
runVcpu(190-71-extra,           #71 Application cycles (scan line 0)
    '---D line 0 no timeout',
    returnTo='vBlankFirst#190')

label('vBlankFirst#72')
ld(lo('vBlankFirst#190'))       #72 Set vCPU return
st([vReturn])                   #73
ld(hi('vBlankFirst#77'),Y)      #74 Jump for more space
jmp(Y,'vBlankFirst#77')         #75
ld(hi(vIRQ_v5),Y)               #76

label('vBlankFirst#190')

# Mitigation for rogue channelMask (3 cycles)
ld([channelMask])               #190 Normalize channelMask, for robustness
anda(0b11111011)                #191
st([channelMask])               #192
# Sound timer
ld([soundTimer])                #193
bne('.sound00')                 #194
suba(1)                         #195
bra('.sound01')                 #196
ld(0)                           #197
label('.sound00')
st([soundTimer])                #196
ld(0xf0)                        #197
label('.sound01')
ora([xoutMask])                 #198
st([xoutMask])                  #199

# New scan line
ld([videoSync0],OUT)            #0 <New scan line start>
label('sound1')
ld([channel])                   #1 Advance to next sound channel
anda([channelMask])             #2
adda(1)                         #3
ld([videoSync1],OUT)            #4 Start horizontal pulse
st([channel],Y)                 #5
ld(0x7f)                        #6 Update sound channel
anda([Y,oscL])                  #7
adda([Y,keyL])                  #8
st([Y,oscL])                    #9
anda(0x80,X)                    #10
ld([X])                         #11
adda([Y,oscH])                  #12
adda([Y,keyH])                  #13
st([Y,oscH])                    #14
anda(0xfc)                      #15
xora([Y,wavX])                  #16
ld(AC,X)                        #17
ld([Y,wavA])                    #18
ld(soundTable>>8,Y)             #19
adda([Y,X])                     #20
bmi(pc()+3)                     #21
bra(pc()+3)                     #22
anda(63)                        #23
ld(63)                          #23(!)
adda([sample])                  #24
st([sample])                    #25

ld([xout])                      #26 Gets copied to XOUT
ld(hi('vBlankLast#34'),Y)       #27 Prepare jumping out of page in last line
ld([videoSync0],OUT)            #28 End horizontal pulse

# Count through the vertical blank interval until its last scan line
ld([videoY])                    #29
bpl('.vBlankLast#32')           #30
adda(2)                         #31
st([videoY])                    #32

# Determine if we're in the vertical sync pulse
suba(1-2*(vBack+vPulse-1))      #33 Prepare sync values
beq('.prepsync#36')             #34 > entering vertical pulse
suba([videoPulse])              #35
beq('.prepsync#38')             #36 > leaving vertical pulse
ld(syncBits)                    #37
bra('.prepsync#40')             #38
label('.prepsync#36')
ld([videoSync1])                #39,36 Avoiding a nop
ld(syncBits^vSync)              #37
label('.prepsync#38')
st([videoSync0])                #38
xora(hSync)                     #39 Precompute, as during the pulse there is no time
label('.prepsync#40')
st([videoSync1])                #40
st(0,[0])                       #41 Reinitialize carry lookup, for robustness

#
videoYInput = 1-2*(vBack-1-1)   # videoY when the 74HC595 has all 8 controller bits
ld([videoY])                    #42
xora(videoYInput)               #43 Check for serial input capture
beq('vbInput#46')               #44
xora(videoYInput)               #45
anda(6)                         #46 Check for sound sample
beq('vbSample#49')              #47
if not WITH_512K_BOARD:
    ld([sample])                #48
else:
    ld([sample],Y)              #48
label('vbNormal#49')
runVcpu(199-49,
        'AB-D line 1-36')       #49 Application cycles (vBlank scan lines without sound sample update)
bra('sound1')                   #199
ld([videoSync0],OUT)            #0 <New scan line start>

# Capture serial input, exactly when the 74HC595 has captured all 8 controller bits
label('vbInput#46')
st(IN, [serialRaw])             #46
if videoYInput & 6 != 0:
    bra('vbNormal#49')          #47
else:
    bra('vbSample#49')          #47
if not WITH_512K_BOARD:
    ld([sample])                #48
else:
    ld([sample],Y)              #48

# Update [xout] with the next sound sample every 4 scan lines.
# Keep doing this on 'videoC equivalent' scan lines in vertical blank.
label('vbSample#49')
if not WITH_512K_BOARD:
    ora(0x0f)                   #49 New sound sample is ready
    anda([xoutMask])            #50
    st([xout])                  #51
    st(sample, [sample])        #52 Reset for next sample
    runVcpu(199-53,
            '--C- line 3-39')   #53 Application cycles (vBlank scan lines with sound sample update)
else:
    ld([xoutMask])              #49
    bmi('.vbSample#52')         #50
    ld([sample])                #51
    bra('.vbSample#54')         #52
    ora(0x0f)                   #53
    label('.vbSample#52')
    ctrl(Y,0xD0)                #52 instead of #43 (wrong by ~2us)
    ora(0x0f)                   #53
    label('.vbSample#54')
    anda([xoutMask])            #54
    st([xout])                  #55
    st(sample, [sample])        #56 Reset for next sample
    runVcpu(199-57,
            '--C- line 3-39')   #57 Application cycles (vBlank scan lines with sound sample update)
bra('sound1')                   #199
ld([videoSync0],OUT)            #0 <New scan line start>

#-----------------------------------------------------------------------

label('.vBlankLast#32')
jmp(Y,'vBlankLast#34')          #32 Jump out of page for space reasons
ld(hi(pc()),Y)                  #33

label('vBlankLast#52')

# Respond to reset button (14 cycles)
# - ResetTimer decrements as long as just [Start] is pressed down
# - Reaching 0 (normal) or 128 (extended) triggers the soft reset sequence
# - Initial value is 128 (or 255 at boot), first decrement, then check
# - This starts vReset -> SYS_Reset_88 -> SYS_Exec_88 -> Reset.gcl -> Main.gcl
# - Main.gcl then recognizes extended presses if resetTimer is 0..127 ("paasei")
# - This requires a full cycle (4s) in the warm boot scenario
# - Or a half cycle (2s) when pressing [Select] down during hard reset
# - This furthermore requires >=1 frame (and <=128) to have passed between
#   reaching 128 and getting through Reset and the start of Main, while [Start]
#   was still pressed so the count reaches <128. Two reasonable expectations.
# - The unintended power-up scenarios of ROMv1 (pulling SER_DATA low, or
#   pressing [Select] together with another button) now don't trigger anymore.

ld([buttonState])               #52 Check [Start] for soft reset
xora(~buttonStart)              #53
bne('.restart#56')              #54
ld([resetTimer])                #55 As long as button pressed
suba(1)                         #56 ... count down the timer
st([resetTimer])                #57
anda(127)                       #58
beq('.restart#61')              #59 Reset at 0 (normal 2s) or 128 (extended 4s)
ld((vReset&255)-2)              #60 Start force reset when hitting 0
bra('.restart#63')              #61 ... otherwise do nothing yet
bra('.restart#64')              #62
label('.restart#56')
wait(62-56)                     #56
ld(128)                         #62 Not pressed, reset the timer
st([resetTimer])                #63
label('.restart#64')
bra('.restart#66')              #64
label('.restart#63')
nop()                           #63,65
label('.restart#61')
st([vPC])                       #61 Point vPC at vReset
ld(vReset>>8)                   #62
st([vPC+1])                     #63
ld(hi('ENTER'))                 #64 Set active interpreter to vCPU
st([vCpuSelect])                #65
label('.restart#66')

# Switch video mode when (only) select is pressed (16 cycles)
# XXX We could make this a vCPU interrupt
ld([buttonState])               #66 Check [Select] to switch modes
xora(~buttonSelect)             #67 Only trigger when just [Select] is pressed
bne('.select#70')               #68

if not WITH_512K_BOARD:
  ld([videoModeC])              #69
  bmi('.select#72')             #70 Branch when line C is off
  ld([videoModeB])              #71 Rotate: Off->D->B->C
  st([videoModeC])              #72
  ld([videoModeD])              #73
  st([videoModeB])              #74
  bra('.select#77')             #75
  label('.select#72')
  ld('nopixels')                #72,76
  ld('pixels')                  #73 Reset: On->D->B->C
  st([videoModeC])              #74
  st([videoModeB])              #75
  nop()                         #76
  label('.select#77')
  st([videoModeD])              #77
else:
  ld([videoModeB])              #69
  xora('nopixels')              #70
  beq('.select#73')             #71
  ld([videoModeD])              #72
  st([videoModeB])              #73
  bra('.select#76')             #74
  ld('nopixels')                #75
  label('.select#73')
  ld('pixels')                  #73
  st([videoModeB])              #74
  nop()                         #75
  label('.select#76')
  st([videoModeD])              #76
  nop()                         #77

ld(255)                         #78
st([buttonState])               #79

if not WITH_128K_BOARD:

  runVcpu(189-80,               #80
          '---D line 40 select',
          returnTo='vBlankEnd#189')
  label('.select#70')
  runVcpu(189-70,               #70
          '---D line 40 no select',
          returnTo='vBlankEnd#189')
  # This must end in 0x1fe and continue
  # with the video loop entry point at 0x1ff
  fillers(until=0xf3)
  label('vBlankEnd#189')
  ld(videoTop_v5>>8,Y)          #189
  ld([Y,videoTop_v5])           #190
  st([videoY])                  #191
  st([frameX])                  #192
  bne(pc()+3)                   #193
  bra(pc()+3)                   #194
  ld('videoA')                  #195
  ld('videoF')                  #195(!)
  st([nextVideo])               #196
  ld([channel])                 #197 Normalize channel for robustness
  anda(0b00000011)              #198
  st([channel])                 #199

else: # WITH_128K_BOARD

  runVcpu(188-80,               #80
          '---D line 40 select',
          returnTo='vBlankEnd#188')
  label('.select#70')
  runVcpu(188-70,               #70
          '---D line 40 no select',
          returnTo='vBlankEnd#188')
  fillers(until=0xf2)
  # Since the entry point is in 0x1fe/#199
  # we have to shift all this by one byte/cycle.
  label('vBlankEnd#188')
  ld(videoTop_v5>>8,Y)          #188
  ld([Y,videoTop_v5])           #189
  st([videoY])                  #190
  st([frameX])                  #191
  bne(pc()+3)                   #192
  bra(pc()+3)                   #193
  ld('videoA')                  #194
  ld('videoF')                  #194(!)
  st([nextVideo])               #195
  ld([channel])                 #196 Normalize channel for robustness
  anda(0b00000011)              #197
  st([channel])                 #198


#-----------------------------------------------------------------------
#
#  $0200 ROM page 2: Video loop visible scanlines
#
#-----------------------------------------------------------------------



if WITH_512K_BOARD:
  assert pc() == 0x1ff            # Enables runVcpu() to re-enter into the next page
  ld(syncBits,OUT)                #200,0 <New scan line start>
  align(0x100, size=0x100)

  # Front porch
  anda([channelMask])             #1 AC is [channel] already!
  adda(1)                         #2
  st([channel],Y)                 #3
  ld(syncBits^hSync,OUT)          #4 Start horizontal pulse (4)

  # Horizontal sync and sound channel update for scanlines outside vBlank
  label('sound2')
  ld(0x7f)                        #5
  anda([Y,oscL])                  #6
  adda([Y,keyL])                  #7
  st([Y,oscL])                    #8
  anda(0x80,X)                    #9
  ld([X])                         #10
  adda([Y,oscH])                  #11
  adda([Y,keyH])                  #12
  st([Y,oscH] )                   #13
  anda(0xfc)                      #14
  xora([Y,wavX])                  #15
  ld(AC,X)                        #16
  ld([Y,wavA])                    #17
  ld(soundTable>>8,Y)             #18
  adda([Y,X])                     #19
  bmi(pc()+3)                     #20
  bra(pc()+3)                     #21
  anda(63)                        #22
  ld(63)                          #22(!)
  adda([sample])                  #23
  st([sample])                    #24
  ld([xout])                      #25 Gets copied to XOUT
  ld(videoTable>>8,Y)             #26 Make Y=1 for all videoABC routines!
  bra([nextVideo])                #27
  ld(syncBits,OUT)                #28 End horizontal pulse

  # Back porch A: first of 4 repeated scan lines
  # - Fetch next Yi and store it for retrieval in the next scan lines
  # - Calculate Xi from dXi and store it as well thanks to a saved cycle.
  label('videoA')
  ld('videoB')                    #29 1st scanline of 4 (always visible)
  st([nextVideo])                 #30
  ld([videoY],X)                  #31
  ld([Y,X])                       #32 Y is already 1
  st([Y,Xpp])                     #33 Just X++
  st([frameY])                    #34
  ld([Y,X])                       #35
  adda([frameX])                  #36
  st([frameX],X)                  #37 I am sure Marcel sought to do this (LB)
  ld([frameY],Y)                  #38
  ld(syncBits)                    #39
  ora([Y,Xpp],OUT)                #40 begin of pixel burst
  runVcpu(200-41,                 #41
          'A--- line 40-520',
          returnTo=0x1ff )

  # Back porch B: second of 4 repeated scan lines
  # - Process double vres
  label('videoB')
  ld('videoC')                    #29
  st([nextVideo])                 #30
  ld([frameY],Y)                  #31
  ld([videoModeC])                #32 New role for videoModeC
  anda(1)                         #33
  adda([frameY])                  #34
  st([frameY])                    #35
  ld([frameX],X)                  #36
  ld(syncBits)                    #37
  bra([videoModeB])               #38
  bra(pc()+2)                     #39
  nop()                           #40 'pixels' or 'nopixels'
  runVcpu(200-41,                 #41
          '-B-- line 40-520',
          returnTo=0x1ff )

  # Back porch C: third of 4 repeated scan lines
  # - Nothing new to for video do as Yi and Xi are known,
  # - This is the time to emit and reset the next sound sample
  label('videoC')
  ld('videoD')                    #29 3rd scanline of 4
  st([nextVideo])                 #30
  ld([sample])                    #31 New sound sample is ready (didn't fit in audio loop)
  ora(0x0f)                       #32
  anda([xoutMask])                #33
  st([xout])                      #34 Update [xout] with new sample (4 channels just updated)
  ld([frameX],X)                  #35
  ld([xoutMask])                  #36
  bmi('videoC#39')                #37
  ld([frameY],Y)                  #38
  ld(syncBits)                    #39
  ora([Y,Xpp], OUT)               #40 Always outputs pixels on C lines
  runVcpu(200-41,                 #41
          '--C- line 40-520 no sound',
          returnTo=0x1ff )
  label('videoC#39')
  ld(syncBits)                    #39
  ora([Y,Xpp], OUT)               #40 Always outputs pixels on C lines
  ld([sample],Y)                  #41
  st(sample, [sample])            #42 Reset for next sample
  ctrl(Y,0xD0);                   #43 Forward audio to PWM (only when audio is active)
  runVcpu(200-44,                 #44
          '--C- line 40-520 sound forwarding',
        returnTo=0x1ff )

  # Back porch D: last of 4 repeated scan lines
  # - Calculate the next frame index
  # - Decide if this is the last line or not
  label('videoD')                 # Default video mode
  ld([frameX], X)                 #29 4th scanline of 4
  ld([videoY])                    #30
  suba((120-1)*2)                 #31
  beq('.lastpixels#34')           #32
  adda(120*2)                     #33 More pixel lines to go
  st([videoY])                    #34
  nop()                           #35
  ld([frameY],Y)                  #36
  ld(syncBits)                    #37
  bra([videoModeD])               #38
  bra(pc()+2)                     #39
  nop()                           #40 'pixels' or 'nopixels'
  nop()                           #41
  ld('videoA')                    #42
  label('videoD#43')
  st([nextVideo])                 #43
  runVcpu(200-44,                 #44
          '---D line 40-520',
          returnTo=0x1ff )

  label('.lastpixels#34')
  if soundDiscontinuity == 1:
    st(sample, [sample])          #34 Sound continuity
  else:
    nop()                         #34
  ld([frameY],Y)                  #35
  ld(syncBits)                    #36
  nop()                           #37
  bra([videoModeD])               #38
  bra(pc()+2)                     #39
  nop()                           #40 'pixels' or 'nopixels'
  bra('videoD#43')                #41
  ld('videoE')                    #42 no more scanlines

  # Back porch "E": after the last line
  # - Go back and and enter vertical blank (program page 2)
  label('videoE') # Exit visible area
  ld(hi('vBlankStart'),Y)         #29 Return to vertical blank interval
  jmp(Y,'vBlankStart')            #30
  ld(syncBits)                    #31

  # Video mode that blacks out one or more pixel lines from the top of screen.
  # This yields some speed, but also frees up screen memory for other purposes.
  # Note: Sound output becomes choppier the more pixel lines are skipped
  # Note: The vertical blank driver leaves 0x80 behind in [videoSync1]
  label('videoF')
  ld([videoSync1])                #29 Completely black pixel line
  adda(0x80)                      #30
  st([videoSync1],X)              #31
  ld([frameX])                    #32
  suba([X])                       #33 Decrements every two VGA scanlines
  beq('.videoF#36')               #34
  st([frameX])                    #35
  bra('.videoF#38')               #36
  label('.videoF#36')
  ld('videoA')                    #36,37 Transfer to visible screen area
  st([nextVideo])                 #37
  label('.videoF#38')
  runVcpu(200-38,
          'F--- line 40-520',
          returnTo=0x1ff )        #38

  fillers(until=0xfc);
  label('pixels')
  ora([Y,Xpp],OUT)                #40
  label('nopixels')
  nop()                           #40

elif WITH_128K_BOARD:

  assert pc() == 0x1fe
  ld([ctrlVideo],X)               #199
  bra('sound3')                   #200,0 <New scan line start>
  align(0x100, size=0x100)
  ctrl(X)                         #1 Reset banking to page1.

  # Back porch A: first of 4 repeated scan lines
  # - Fetch next Yi and store it for retrieval in the next scan lines
  # - Calculate Xi from dXi, but there is no cycle time left to store it as well
  label('videoA')
  ld('videoB')                    #29 1st scanline of 4 (always visible)
  st([nextVideo])                 #30
  ld(videoTable>>8,Y)             #31
  ld([videoY],X)                  #32
  ld([Y,X])                       #33
  st([Y,Xpp])                     #34 Just X++
  st([frameY])                    #35
  ld([Y,X])                       #36
  adda([frameX],X)                #37
  label('pixels')
  ld([frameY],Y)                  #38
  ld(syncBits)                    #39

  # Stream 160 pixels from memory location <Yi,Xi> onwards
  # Superimpose the sync signal bits to be robust against misprogramming
  for i in range(qqVgaWidth):
    ora([Y,Xpp],OUT)              #40-199 Pixel burst
  ld(syncBits,OUT)                #0 <New scan line start> Back to black

  # Front porch
  ld([channel])                   #1 Advance to next sound channel
  label('sound3')                 # Return from vCPU interpreter
  anda([channelMask])             #2
  adda(1)                         #3
  ld(syncBits^hSync,OUT)          #4 Start horizontal pulse

  # Horizontal sync and sound channel update for scanlines outside vBlank
  label('sound2')
  st([channel],Y)                 #5
  ld(0x7f)                        #6
  anda([Y,oscL])                  #7
  adda([Y,keyL])                  #8
  st([Y,oscL])                    #9
  anda(0x80,X)                    #10
  ld([X])                         #11
  adda([Y,oscH])                  #12
  adda([Y,keyH])                  #13
  st([Y,oscH] )                   #14
  anda(0xfc)                      #15
  xora([Y,wavX])                  #16
  ld(AC,X)                        #17
  ld([Y,wavA])                    #18
  ld(soundTable>>8,Y)             #19
  adda([Y,X])                     #20
  bmi(pc()+3)                     #21
  bra(pc()+3)                     #22
  anda(63)                        #23
  ld(63)                          #23
  adda([sample])                  #24
  st([sample])                    #25

  ld([xout])                      #26 Gets copied to XOUT
  bra([nextVideo])                #27
  ld(syncBits,OUT)                #28 End horizontal pulse

  # Back porch B: second of 4 repeated scan lines
  # - Recompute Xi from dXi and store for retrieval in the next scan lines
  label('videoB')
  ld('videoC')                    #29 2nd scanline of 4
  st([nextVideo])                 #30
  ld(videoTable>>8,Y)             #31
  ld([videoY])                    #32
  adda(1,X)                       #33
  ld([frameX])                    #34
  adda([Y,X])                     #35
  bra([videoModeB])               #36
  st([frameX],X)                  #37 Store in RAM and X

  # Back porch C: third of 4 repeated scan lines
  # - Nothing new to for video do as Yi and Xi are known,
  # - This is the time to emit and reset the next sound sample
  label('videoC')
  ld('videoD')                    #29 3rd scanline of 4
  st([nextVideo])                 #30
  ld([sample])                    #31 New sound sample is ready (didn't fit in audio loop)
  ora(0x0f)                       #32
  anda([xoutMask])                #33
  st([xout])                      #34 Update [xout] with new sample (4 channels just updated)
  st(sample, [sample])            #35 Reset for next sample
  bra([videoModeC])               #36
  ld([frameX],X)                  #37

  # Back porch D: last of 4 repeated scan lines
  # - Calculate the next frame index
  # - Decide if this is the last line or not
  label('videoD')                 # Default video mode
  ld([frameX], X)                 #29 4th scanline of 4
  ld([videoY])                    #30
  suba((120-1)*2)                 #31
  beq('.lastpixels#34')           #32
  adda(120*2)                     #33 More pixel lines to go
  st([videoY])                    #34
  ld('videoA')                    #35
  bra([videoModeD])               #36
  st([nextVideo])                 #37

  label('.lastpixels#34')
  if soundDiscontinuity == 1:
    st(sample, [sample])          #34 Sound continuity
  else:
    nop()                         #34
  ld('videoE')                    #35 No more pixel lines to go
  bra([videoModeD])               #36
  st([nextVideo])                 #37

  # Back porch "E": after the last line
  # - Go back and and enter vertical blank (program page 2)
  label('videoE') # Exit visible area
  ld(hi('vBlankStart'),Y)         #29 Return to vertical blank interval
  jmp(Y,'vBlankStart')            #30
  ld(syncBits)                    #31

  # Video mode that blacks out one or more pixel lines from the top of screen.
  # This yields some speed, but also frees up screen memory for other purposes.
  # Note: Sound output becomes choppier the more pixel lines are skipped
  # Note: The vertical blank driver leaves 0x80 behind in [videoSync1]
  label('videoF')
  ld([videoSync1])                #29 Completely black pixel line
  adda(0x80)                      #30
  st([videoSync1],X)              #31
  ld([frameX])                    #32
  suba([X])                       #33 Decrements every two VGA scanlines
  beq('.videoF#36')               #34
  st([frameX])                    #35
  bra('nopixels')                 #36
  label('.videoF#36')
  ld('videoA')                    #36,37 Transfer to visible screen area
  st([nextVideo])                 #37
  #
  # Alternative for pixel burst: faster application mode
  label('nopixels')
  ld([ctrlCopy],X)                #38
  ctrl(X)                         #39
  runVcpu(199-40,
          'FBCD line 40-520',
          returnTo=0x1fe)         #40 Application interpreter (black scanlines)

else:  # NORMAL VIDEO CODE

  assert pc() == 0x1ff
  bra('sound3')                   #200,0 <New scan line start>
  align(0x100, size=0x100)
  ld([channel])                   #1 AC already contains [channel]

  # Back porch A: first of 4 repeated scan lines
  # - Fetch next Yi and store it for retrieval in the next scan lines
  # - Calculate Xi from dXi, but there is no cycle time left to store it as well
  label('videoA')
  ld('videoB')                    #29 1st scanline of 4 (always visible)
  st([nextVideo])                 #30
  ld(videoTable>>8,Y)             #31
  ld([videoY],X)                  #32
  ld([Y,X])                       #33
  st([Y,Xpp])                     #34 Just X++
  st([frameY])                    #35
  ld([Y,X])                       #36
  adda([frameX],X)                #37
  label('pixels')
  ld([frameY],Y)                  #38
  ld(syncBits)                    #39

  # Stream 160 pixels from memory location <Yi,Xi> onwards
  # Superimpose the sync signal bits to be robust against misprogramming
  for i in range(qqVgaWidth):
    ora([Y,Xpp],OUT)              #40-199 Pixel burst
  ld(syncBits,OUT)                #0 <New scan line start> Back to black

  # Front porch
  ld([channel])                   #1 Advance to next sound channel
  label('sound3')                 # Return from vCPU interpreter
  anda([channelMask])             #2
  adda(1)                         #3
  ld(syncBits^hSync,OUT)          #4 Start horizontal pulse

  # Horizontal sync and sound channel update for scanlines outside vBlank
  label('sound2')
  st([channel],Y)                 #5
  ld(0x7f)                        #6
  anda([Y,oscL])                  #7
  adda([Y,keyL])                  #8
  st([Y,oscL])                    #9
  anda(0x80,X)                    #10
  ld([X])                         #11
  adda([Y,oscH])                  #12
  adda([Y,keyH])                  #13
  st([Y,oscH] )                   #14
  anda(0xfc)                      #15
  xora([Y,wavX])                  #16
  ld(AC,X)                        #17
  ld([Y,wavA])                    #18
  ld(soundTable>>8,Y)             #19
  adda([Y,X])                     #20
  bmi(pc()+3)                     #21
  bra(pc()+3)                     #22
  anda(63)                        #23
  ld(63)                          #23(!)
  adda([sample])                  #24
  st([sample])                    #25

  ld([xout])                      #26 Gets copied to XOUT
  bra([nextVideo])                #27
  ld(syncBits,OUT)                #28 End horizontal pulse

  # Back porch B: second of 4 repeated scan lines
  # - Recompute Xi from dXi and store for retrieval in the next scan lines
  label('videoB')
  ld('videoC')                    #29 2nd scanline of 4
  st([nextVideo])                 #30
  ld(videoTable>>8,Y)             #31
  ld([videoY])                    #32
  adda(1,X)                       #33
  ld([frameX])                    #34
  adda([Y,X])                     #35
  bra([videoModeB])               #36
  st([frameX],X)                  #37 Store in RAM and X

  # Back porch C: third of 4 repeated scan lines
  # - Nothing new to for video do as Yi and Xi are known,
  # - This is the time to emit and reset the next sound sample
  label('videoC')
  ld('videoD')                    #29 3rd scanline of 4
  st([nextVideo])                 #30
  ld([sample])                    #31 New sound sample is ready (didn't fit in audio loop)
  ora(0x0f)                       #32
  anda([xoutMask])                #33
  st([xout])                      #34 Update [xout] with new sample (4 channels just updated)
  st(sample, [sample])            #35 Reset for next sample
  bra([videoModeC])               #36
  ld([frameX],X)                  #37

  # Back porch D: last of 4 repeated scan lines
  # - Calculate the next frame index
  # - Decide if this is the last line or not
  label('videoD')                 # Default video mode
  ld([frameX], X)                 #29 4th scanline of 4
  ld([videoY])                    #30
  suba((120-1)*2)                 #31
  beq('.lastpixels#34')           #32
  adda(120*2)                     #33 More pixel lines to go
  st([videoY])                    #34
  ld('videoA')                    #35
  bra([videoModeD])               #36
  st([nextVideo])                 #37

  label('.lastpixels#34')
  if soundDiscontinuity == 1:
    st(sample, [sample])          #34 Sound continuity
  else:
    nop()                         #34
  ld('videoE')                    #35 No more pixel lines to go
  bra([videoModeD])               #36
  st([nextVideo])                 #37

  # Back porch "E": after the last line
  # - Go back and and enter vertical blank (program page 2)
  label('videoE') # Exit visible area
  ld(hi('vBlankStart'),Y)         #29 Return to vertical blank interval
  jmp(Y,'vBlankStart')            #30
  ld(syncBits)                    #31

  # Video mode that blacks out one or more pixel lines from the top of screen.
  # This yields some speed, but also frees up screen memory for other purposes.
  # Note: Sound output becomes choppier the more pixel lines are skipped
  # Note: The vertical blank driver leaves 0x80 behind in [videoSync1]
  label('videoF')
  ld([videoSync1])                #29 Completely black pixel line
  adda(0x80)                      #30
  st([videoSync1],X)              #31
  ld([frameX])                    #32
  suba([X])                       #33 Decrements every two VGA scanlines
  beq('.videoF#36')               #34
  st([frameX])                    #35
  bra('nopixels')                 #36
  label('.videoF#36')
  ld('videoA')                    #36,37 Transfer to visible screen area
  st([nextVideo])                 #37
  #
  # Alternative for pixel burst: faster application mode
  label('nopixels')
  runVcpu(200-38,
          'FBCD line 40-520',
          returnTo=0x1ff)         #38 Application interpreter (black scanlines)


#-----------------------------------------------------------------------
#
#  $0300 ROM page 3: Application interpreter primary page
#
#-----------------------------------------------------------------------

# Enter the timing-aware application interpreter (aka virtual CPU, vCPU)
#
# This routine will execute as many as possible instructions in the
# allotted time. When time runs out, it synchronizes such that the total
# duration matches the caller's request. Durations are counted in `ticks',
# which are multiples of 2 clock cycles.
#
# Synopsis: Use the runVcpu() macro as entry point

# We let 'ENTER' begin one word before the page boundary, for a bit extra
# precious space in the packed interpreter code page. Although ENTER's
# first instruction is bra() which normally doesn't cross page boundaries,
# in this case it will still jump into the right space, because branches
# from $xxFF land in the next page anyway.

fillers(until=0xff)
label('ENTER')
bra('.next2')                   #0 Enter at '.next2' (so no startup overhead)
# --- Page boundary ---
align(0x100,size=0x100)
label('NEXTY')                  # Alternative for REENTER
ld([vPC+1],Y)                   #1

# Fetch next instruction and execute it, but only if there are sufficient
# ticks left for the slowest instruction.
label('NEXT')
adda([vTicks])                  #0 Track elapsed ticks (actually counting down: AC<0)
blt('EXIT')                     #1 Escape near time out
label('.next2')
st([vTicks])                    #2
ld([vPC])                       #3 Advance vPC
adda(2)                         #4
st([vPC],X)                     #5
ld([Y,X])                       #6 Fetch opcode (actually a branch target)
st([Y,Xpp])                     #7 Just X++
bra(AC)                         #8 Dispatch
ld([Y,X])                       #9 Prefetch operand

# Resync with video driver and transfer control
label('EXIT')
adda(maxTicks)                  #3
label('RESYNC')
bgt(pc()&255)                   #4 Resync
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7 To video driver
ld([channel])                   #8 with channel in AC
assert vCPU_overhead ==          9

# Instruction LDWI: Load immediate word constant (vAC=D), 20 cycles
label('LDWI')
st([vAC])                       #10
st([Y,Xpp])                     #11 Just X++
ld([vPC])                       #12 Advance vPC one more
adda(1)                         #13
st([vPC])                       #14
bra('ldw#17')                   #15
ld([Y,X])                       #16 Fetch second operand

# Instruction NEGV (18 vv) [26 cycles]
# * Negates word [vv]:=-[vv]
label('NEGV_v7')
ld(hi('negv#13'),Y)             #10
jmp(Y,'negv#13')                #11+overlap

# Instruction LD: Load byte from zero page (vAC=[D]), 18 cycles
label('LD')
ld(AC,X)                        #10
bra('ld#13')                    #11
ld([X])                         #13

# Helper for INC.
label('inc#14')
bra('ld#16')                    #14
st([X])                         #15

# Instruction CMPHS: Adjust high byte for signed compare (vACH=XXX), 20-26 cycles
label('CMPHS_v5')
ld(hi('cmphs#13'),Y)            #10
jmp(Y,'cmphs#13')               #11
#ld(AC,X)                       #12 Overlap
#
# Instruction LDW: Load word from zero page (vAC=[D]+256*[D+1]), 20 cycles
label('LDW')
ld(AC,X)                        #10,12
adda(1)                         #11
st([vTmp])                      #12 Address of high byte
ld([X])                         #13
ld([vTmp],X)                    #14
st([vAC])                       #15
ld([X])                         #16
label('ldw#17')
st([vAC+1])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19

# Instruction STW: Store word in zero page ([D],[D+1]=vAC&255,vAC>>8), 20 cycles
label('STW')
ld(AC,X)                        #10
ld(0,Y)                         #11
ld([vAC])                       #12
st([Y,Xpp])                     #13
ld([vAC+1])                     #14
st([Y,X])                       #15
bra('REENTER')                  #16
ld(-20/2)                       #17

# Instruction ADDHI (33 xx), 16 cycles
# * Add constant xx to vACH.
# * To be used in conjunction with ADDI add a 16 bits constant
label('ADDHI_v7')
bra('ldi#12')
adda([vAC+1])

# Instruction PREFIX35: (used to be BCC)
label('BCC')
label('PREFIX35')
st([Y,Xpp])                     #10
ld(hi('PREFIX35_PAGE'),Y)       #11
jmp(Y,AC)                       #12
ld([vPC+1],Y)                   #13

# Instruction POKEA (39 xx), 22 cycles
# * Store word [xx] at location [vAC]
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2053#p2053
#   Section 2. "POKE and DOKE work backwards"
label('POKEA_v7')
ld(hi('pokea#13'),Y)            #10,12
jmp(Y,'pokea#13')               #11

# Instruction DOKEA (3b xx), 28 cycles
# * Store word [xx] at location [vAC]
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2053#p2053
#   Section 2. "POKE and DOKE work backwards"
label('DOKEA_v7')
ld(hi('dokea#13'),Y)            #10
jmp(Y,'dokea#13')               #11+overlap

# Instruction DEEKA (3d xx), 30 cycles
# * Load word at location [vAC] and store into [xx]
# * Trashes sysArgs7 but can DEEK(sysArgs6or7)
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2053#p2053
#   Section 2. "POKE and DOKE work backwards"
label('DEEKA_v7')
ld(hi('deeka#13'),Y)            #10,12
jmp(Y,'deeka#13')               #11

# Instruction JEQ (3f ll hh), 24/26 cycles (was EQ)
# * Branch if zero (if(vACL==0)vPC=hhll[+2])
# * Original idea from at67
label('EQ')
label('JEQ_v7')
ld(hi('jeq#13'),Y)              #10,12
jmp(Y,'jeq#13')                 #11

# Instruction DEEKV (41 vv), 28 cycles
# * shortcut for LDW(vv);DEEK()
# * Original idea from at67
label('DEEKV_v7')
ld(hi('deekv#13'),Y)            #10,12
jmp(Y,'deekv#13')               #11
st([vTmp])                      #12

# Instruction DOKEQ (44 ii), 22 cycles
# * Store immediate ii into word pointed by vAC
label('DOKEQ_v7')
ld(hi('dokeq#13'),Y)            #10,12
jmp(Y,'dokeq#13')               #11

# Instruction POKEQ (46 ii), 20 cycles
# * Store immediate ii into byte pointed by vAC
label('POKEQ_v7')
ld(hi('pokeq#13'),Y)            #10,12
jmp(Y,'pokeq#13')               #11

# Instruction MOVQB (48 vv ii), 26 cycles
# * Store immediate ii into byte [vv]:=ii
label('MOVQB_v7')
ld(hi('movqb#13'),Y)            #10
jmp(Y,'movqb#13')               #11

# Instruction MOVQW (4a vv ii), 28 cycles
# * Store immediate ii into word [vv]:=ii [vv+1]:=0
label('MOVQW_v7')
ld(hi('movqw#13'),Y)            #10
jmp(Y,'movqw#13')               #11
ld([vPC+1],Y)                   #12

# Instruction JGT (4d ll hh), 22-24/26 cycles (was GT)
# * Branch if positive (if(vACL>0)vPC=hhll[+2])
# * Original idea from at67
label('GT')
label('JGT_v7')
ld(hi('jgt#13'),Y)              #10,12
jmp(Y,'jgt#13')                 #11
ld([vAC+1])                     #12

# Instruction JLT (50 ll hh), 22/24 cycles (was LT)
# * Branch if negative (if(vACL<0)vPC=hhll[+2])
# * Original idea from at67
label('LT')
label('JLT_v7')
ld(hi('jlt#13'),Y)              #10
jmp(Y,'jlt#13')                 #11
ld([vAC+1])                     #12

# Instruction JGE (53 ll hh), 22/24 cycles (was GE)
# * Branch if positive or zero (if(vACL>=0)vPC=hhll[+2])
# * Original idea from at67
label('GE')
label('JGE_v7')
ld(hi('jge#13'),Y)              #10
jmp(Y,'jge#13')                 #11
ld([vAC+1])                     #12

# Instruction JLE (56 ll hh), 22-24/26 cycles (was LE)
# * Branch if negative or zero (if(vACL<=0)vPC=hhll[+2])
# * Original idea from at67
label('JLE_v7')
ld(hi('jle#13'),Y)              #10
jmp(Y,'jle#13')                 #11
ld([vAC+1])                     #12

# Instruction LDI: Load immediate small positive constant (vAC=D), 16 cycles
label('LDI')
st([vAC])                       #10
ld(0)                           #11
label('ldi#12')
st([vAC+1])                     #12
bra('NEXTY')                    #13
ld(-16/2)                       #14

# Instruction ST: Store byte in zero page ([D]=vAC&255), 16 cycles
label('ST')
ld(AC,X)                        #10,15
ld([vAC])                       #11
st([X])                         #12
bra('NEXTY')                    #13
ld(-16/2)                       #14

# Instruction POP (63), 30 cycles (38 when crossing a page)
# * Pop vLR from stack: vLR=*vSP vSP+=2
label('POP')
ld(hi('pop#13'),Y)              #10
jmp(Y,'pop#13')                 #11
ld([vSP+1],Y)                   #12

# Instruction ADDV (66 vv), 30 cycles
# * Add vAC to word [vv]
label('ADDV_v7')
ld(hi('addv#13'),Y)             #10,12
jmp(Y,'addv#13')                #11

# Instruction SUBV (68 vv), 30 cycles
# * Subtract vAC from word [vv]
label('SUBV_v7')
ld(hi('subv#13'),Y)             #10,12
jmp(Y,'subv#13')                #11

# Instruction LDXW (6a vv ll hh), 28+30 cycles
# * Load word indexed: vAC := *([vv]+hhll)
label('LDXW_v7')
ld(hi('ldxw#13'),Y)             #10,12
jmp(Y,'ldxw#13')                #11

# Instruction STXW (6c vv ll hh), 28+30 cycles
# * Store word indexed: *([vv]+hhll) := vAC
label('STXW_v7')
ld(hi('stxw#13'),Y)             #10,12
jmp(Y,'stxw#13')                #11

# Instruction LDSB (6e xx), 24 cycles
# Load signed byte. vACL=[xx] vACH=([xx]&0x80)?$ff:$00
label('LDSB_v7')
ld(hi('ldsb#13'),Y)             #10,12
jmp(Y, 'ldsb#13')               #11

# Instruction INCV (70 vv), 22-28 cycles
# * Increment word [vv]
label('INCV_v7')
ld(hi('incv#13'),Y)             #10,12
jmp(Y,'incv#13')                #11

# Instruction JNE (72 ii jj), 24/26 cycles (was NE)
# * Branch if not zero (if(vACL!=0)vPC=iijj)
# * Original idea from at67
label('NE')
label('JNE_v7')
ld(hi('jne#13'),Y)              #10,12
jmp(Y,'jne#13')                 #11
nop()                           #12

# Instruction PUSH (75), 28 cycles (38 when crossing a page)
# * Push vLR on stack: vSP-=2 *vSP=vLR
label('PUSH')
ld(hi('push#13'),Y)             #10
jmp(Y,'push#13')                #11
ld([vSP+1],Y)                   #12

# Instruction slot @ 0x78 (formerly LDNI)
ld(hi('reset'),Y)               #10
jmp(Y,'reset')                  #11

# Instruction DBNE (7a vv ii), 24/26 cycles
# * Decrement byte vv and branches to ii+2 if nonzero
label('DBNE_v7')
ld(hi('dbne#13'),Y)             #10
jmp(Y,'dbne#13')                #11
ld(AC,X)                        #12

# Instruction MULQ (7d kk)
# * Execute multiplication code 0x1kk
# * 1*:shift; 01*:add; 00?*:sub; allzero:exit
label('MULQ_v7')
ld(hi('mulq#13'),Y)
jmp(Y,'mulq#13')

# Instruction LUP: ROM lookup (vAC=ROM[vAC+D]), 26 cycles
label('LUP')
ld(hi('lup#13'),Y)              #10
jmp(Y,'lup#13')                 #11
adda([vAC])                     #12

# Instruction ANDI: Logical-AND with small constant (vAC&=D), 18 cycles
label('ANDI')
anda([vAC])                     #10
bra('ld#13')                    #11
nop()                           #12

# Instruction CALLI: Goto immediate address and remember vPC (vLR,vPC=vPC+3,$HHLL-2), 28 cycles
label('CALLI_v5')
ld(hi('calli#13'),Y)            #10
jmp(Y,'calli#13')               #11
ld([vPC])                       #12

# Instruction ORI: Logical-OR with small constant (vAC|=D), 14 cycles
label('ORI')
ora([vAC])                      #10
st([vAC])                       #11
bra('NEXT')                     #12
ld(-14/2)                       #13

# Instruction XORI: Logical-XOR with small constant (vAC^=D), 14 cycles
label('XORI')
xora([vAC])                     #10
st([vAC])                       #11
bra('NEXT')                     #12
ld(-14/2)                       #13

# Instruction BRA: Branch unconditionally (vPC=(vPC&0xff00)+D), 14 cycles
label('BRA')
st([vPC])                       #10
bra('NEXTY')                    #11
ld(-14/2)                       #12

# Instruction INC: Increment zero page byte ([D]++), 18 cycles
label('INC')
ld(AC,X)                        #10,13
ld([X])                         #11
bra('inc#14')                   #12
adda(1)                         #13

# Instruction CMPHU: Adjust high byte for unsigned compare (vACH=XXX), 20-26 cycles
label('CMPHU_v5')
ld(hi('cmphu#13'),Y)            #10
jmp(Y,'cmphu#13')               #11
#ld(AC,X)                       #12 Overlap
#
# Instruction ADDW: Word addition with zero page (vAC+=[D]+256*[D+1]), 28 cycles
label('ADDW')
# The non-carry paths could be 26 cycles at the expense of (much) more code.
# But a smaller size is better so more instructions fit in this code page.
# 28 cycles is still 4.5 usec. The 6502 equivalent takes 20 cycles or 20 usec.
ld(AC,X)                        #10,12 Address of low byte to be added
adda(1)                         #11
st([vTmp])                      #12 Address of high byte to be added
ld([vAC])                       #13 Add the low bytes
adda([X])                       #14
st([vAC])                       #15 Store low result
bmi('.addw#18')                 #16 Now figure out if there was a carry
suba([X])                       #17 Gets back the initial value of vAC
bra('.addw#20')                 #18
ora([X])                        #19 Carry in bit 7
label('.addw#18')
anda([X])                       #18 Carry in bit 7
nop()                           #19
label('.addw#20')
anda(0x80,X)                    #20 Move carry to bit 0
ld([X])                         #21
adda([vAC+1])                   #22 Add the high bytes with carry
ld([vTmp],X)                    #23
adda([X])                       #24
st([vAC+1])                     #25 Store high result
bra('NEXT')                     #26
ld(-28/2)                       #27

# Instruction PEEK: Read byte from memory (vAC=[vAC]), 26 cycles
label('PEEK')
ld(hi('peek'),Y)                #10
jmp(Y,'peek')                   #11

# Instruction slot @ 0xaf
ld(hi('reset'),Y)               #10
jmp(Y,'reset')                  #11

# Instruction MOVIW (b1 vv hh ll), 30 cycles
# * Stores immediate $hhll into word variable [vv]
# * Trashes sysArgs[7] but vv=sysArgs[6-7] works
label('MOVIW_v7')
ld(hi('moviw#13'),Y)            #10
jmp(Y,'moviw#13')               #11
st([sysArgs+7])                 #12

# Instruction SYS: Native call, <=256 cycles (<=128 ticks, in reality less)
#
# The 'SYS' vCPU instruction first checks the number of desired ticks given by
# the operand. As long as there are insufficient ticks available in the current
# time slice, the instruction will be retried. This will effectively wait for
# the next scan line if the current slice is almost out of time. Then a jump to
# native code is made. This code can do whatever it wants, but it must return
# to the 'REENTER' label when done. When returning, AC must hold (the negative
# of) the actual consumed number of whole ticks for the entire virtual
# instruction cycle (from NEXT to NEXT). This duration may not exceed the prior
# declared duration in the operand + 28 (or maxTicks). The operand specifies the
# (negative) of the maximum number of *extra* ticks that the native call will
# need. The GCL compiler automatically makes this calculation from gross number
# of cycles to excess number of ticks.
# SYS functions can modify vPC to implement repetition. For example to split
# up work into multiple chucks.
label('SYS')
adda([vTicks])                  #10
blt('.sys#13')                  #11
ld([sysFn+1],Y)                 #12
jmp(Y,[sysFn])                  #13
#dummy()                        #14 Overlap
#
# Instruction SUBW (b8 vv), 30 cycles
# * Subtract [vv] from vAC (AC-=[vv]+256*[vv+1])
label('SUBW')
ld(hi('subw#13'),Y)             #10,14
jmp(Y,'subw#13')                #11
ld(hi('NEXTY'),Y)               #12

# Instruction MOVW (bb dd ss), 36 cycles
# * Move word [ss..ss+1] to [dd..dd+1].
# * Trashes sysArgs7
label('MOVW_v7')
st([sysArgs+7])                 #10 destination operand
st([Y,Xpp])                     #11
ld([Y,X])                       #12 source operand
ld(hi('movw#16'),Y)             #13
jmp(Y,'movw#16')                #14
adda(1,X)                       #15

# Continue LD/ANDI/INC
label('ld#13')
st([vAC])                       #13 LD,ANDI
ld(0)                           #14
st([vAC+1])                     #15
label('ld#16')
bra('NEXT')                     #16 INC
ld(-18/2)                       #17

# Instruction ADDSV (c6 vv ss), 30 cycles + 24/26 when crossing half page
# * Add signed immediate ss to word [vv..vv+1].
label('ADDSV_v7')
ld(hi('addsv#13'),Y)            #10
jmp(Y,'addsv#13')               #11 + overlap

# SYS restart
label('.sys#13')
ld(hi('.sys#16'),Y)              #13,12
jmp(Y,'.sys#16')                 #14

# SYS call re-entry code (fixed address)
label('REENTER_28')
ld(-28/2)                       #25
label('REENTER')
bra('NEXT')                     #26 Return from SYS calls
ld([vPC+1],Y)                   #27

# Instruction DEF: Define data or code (vAC,vPC=vPC+2,(vPC&0xff00)+D), 24 cycles
label('DEF')
ld(hi('def#13'),Y)              #10
jmp(Y,'def#13')                 #11
#st([vTmp])                     #12 Overlap
#
# Instruction CALL: Goto address and remember vPC (vLR,vPC=vPC+2,[D]+256*[D+1]-2), 30 cycles
label('CALL')
st([vTmp])                      #10,12
ld(hi('call#14'),Y)             #11
jmp(Y,'call#14')                #12
adda(1,X)                       #13

# Instruction CMPWS (d3 vv), 26-30 cycles
# * Signed compare of vAC and [vv]. Faster than CMPHS+SUBW
label('CMPWS_v7')
ld(hi('cmpws#13'),Y)            #10
jmp(Y,'cmpws#13')               #11
st([vTmp])                      #12

# Instruction CMPWU (d6 vv), 26-30 cycles
# * Unsigned compare of vAC and [vv]. Faster than CMPHU+SUBW
label('CMPWU_v7')
ld(hi('cmpwu#13'),Y)            #10
jmp(Y,'cmpwu#13')               #11
st([vTmp])                      #12

# Instruction CMPIS (d9 ii), 22-30 cycles
# * Signed compare of vAC and byte ii.
label('CMPIS_v7')
ld(hi('cmpis#13'),Y)            #10
jmp(Y,'cmpis#13')               #11

# Instruction CMPIU (db ii), 24-30 cycles
# * Unsigned compare of vAC and byte ii.
label('CMPIU_v7')
ld(hi('cmpiu#13'),Y)            #10,12
jmp(Y,'cmpiu#13')               #11

# Instruction PEEKV (dd vv), 28 cycles
# * Shortcut for LDW(vv);DEEK()
label('PEEKV_v7')
ld(hi('peekv#13'),Y)            #10,12
jmp(Y,'peekv#13')               #11

# Instruction ALLOC: Create or destroy stack frame (vSP+=D), 24/28-30 cycles
label('ALLOC')
ld(hi('alloc#13'),Y)            #10,12
jmp(Y,'alloc#13')               #11

# Instruction PEEKA (e1 xx), 24 cycles
# * Load byte at location [vAC] and store into byte [xx]
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2053#p2053
#   Section 2. "POKE and DOKE work backwards"
label('PEEKA_v7')
ld(hi('peeka#13'),Y)            #10,12
jmp(Y,'peeka#13')               #11

# The instructions below are all implemented in the second code page. Jumping
# back and forth makes each 6 cycles slower, but it also saves space in the
# primary page for the instructions above. Most of them are in fact not very
# critical, as evidenced by the fact that they weren't needed for the first
# Gigatron applications (Snake, Racer, Mandelbrot, Loader). By providing them
# in this way, at least they don't need to be implemented as a SYS extension.

# Instruction ADDI: Add small positive constant (vAC+=D), 24-26 cycles
label('ADDI')
ld(hi('addi#13'),Y)             #10,12
jmp(Y,'addi#13')                #11
st([vTmp])                      #12

# Instruction SUBI: Subtract small positive constant (vAC+=D), 24-26 cycles
label('SUBI')
ld(hi('subi#13'),Y)             #10
jmp(Y,'subi#13')                #11
st([vTmp])                      #12

# Instruction LSLW: Logical shift left (vAC<<=1), 26-28 cycles
# Useful, because ADDW can't add vAC to itself. Also more compact.
label('LSLW')
ld(hi('lslw#13'),Y)             #10
jmp(Y,'lslw#13')                #11
ld([vPC])                       #12

# Instruction STLW: (ec xx) 26 cycles (36 when vSPH!=0)
# * Store word in stack frame: *(vSP + xx) := vAC
label('STLW')
ld(hi('stlw#13'),Y)             #10
jmp(Y,'stlw#13')                #11
#dummy()                        #12 Overlap
#
# Instruction LDLW: (ee xx) 26 cycles (36/38 when vSPH!=0)
# * Load word from stack frame: vAC := *(vSP + xx)
label('LDLW')
ld(hi('ldlw#13'),Y)             #10,12
jmp(Y,'ldlw#13')                #11
#st([vTmp])                     #12 Overlap
#
# Instruction POKE: Write byte in memory ([[D+1],[D]]=vAC&255), 28 cycles
label('POKE')
st([vTmp])                      #10,12
ld(hi('poke#14'),Y)             #11
jmp(Y,'poke#14')                #12 Overlap

# Instruction DOKE: Write word in memory ([[D+1],[D]],[[D+1],[D]+1]=vAC&255,vAC>>8), 28 cycles
label('DOKE')
ld(hi('doke'),Y)                #10,13
jmp(Y,'doke')                   #11
st([vTmp])                      #12

# Instruction DEEK: Read word from memory (vAC=[vAC]+256*[vAC+1]), 28 cycles
label('DEEK')
ld(hi('deek'),Y)                #10
jmp(Y,'deek')                   #11
#dummy()                        #12 Overlap
#
# Instruction ANDW: Word logical-AND with zero page (vAC&=[D]+256*[D+1]), 28 cycles
label('ANDW')
ld(hi('andw'),Y)                #10,12
jmp(Y,'andw')                   #11
#dummy()                        #12 Overlap
#
# Instruction ORW: Word logical-OR with zero page (vAC|=[D]+256*[D+1]), 28 cycles
label('ORW')
ld(hi('orw'),Y)                 #10,12
jmp(Y,'orw')                    #11
#dummy()                        #12 Overlap
#
# Instruction XORW: Word logical-XOR with zero page (vAC^=[D]+256*[D+1]), 26 cycles
label('XORW')
ld(hi('xorw'),Y)                #10,12
jmp(Y,'xorw')                   #11
st([vTmp])                      #12

# Instruction RET: Function return (vPC=vLR-2), 20 cycles
label('RET')
ld([vLR])                       #10
assert pc()&255 == 0

#-----------------------------------------------------------------------
#
#  $0400 ROM page 4: Application interpreter extension
#
#-----------------------------------------------------------------------
align(0x100, size=0x100)

# (Continue RET)
suba(2)                         #11
st([vPC])                       #12
ld([vLR+1])                     #13
st([vPC+1])                     #14
ld(hi('REENTER'),Y)             #15
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17

# DEF implementation
label('def#13')
ld([vPC])                       #13
adda(2)                         #14
st([vAC])                       #15
ld([vPC+1])                     #16
st([vAC+1])                     #17
ld([vTmp])                      #18
st([vPC])                       #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

# LDSB implementation
label('ldsb#13')
ld(AC,X)                        #13
ld([X])                         #14
st([vAC])                       #15
bmi(pc()+3)                     #16
bra(pc()+3)                     #17
ld(0)                           #18
ld(0xff)                        #18
st([vAC+1])                     #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

# ADDI implementation
label('addi#13')
ld(hi('NEXTY'),Y)               #13
adda([vAC])                     #14
st([vAC])                       #15 Store low result
bmi('.addi#18')                 #16 Now figure out if there was a carry
suba([vTmp])                    #17 Gets back the initial value of vAC
ora([vTmp])                     #18 Carry in bit 7
bmi('.addi#21c')                #19
ld(1)                           #20
label('.addi#21n')
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22
label('.addi#18')
anda([vTmp])                    #18 Carry in bit 7
bpl('.addi#21n')                #19
ld(1)                           #20
label('.addi#21c')
adda([vAC+1])                   #21 Add the high bytes with carry
st([vAC+1])                     #22 Store high result
jmp(Y,'NEXTY')                  #24
ld(-26/2)                       #25

# LSLW implementation
label('lslw#13')
suba(1)                         #13
st([vPC])                       #14
ld([vAC])                       #15
ld(hi('NEXTY'),Y)               #16
bmi('lslw#19')                  #17
adda(AC)                        #18
st([vAC])                       #19
ld([vAC+1])                     #20
adda(AC)                        #21
st([vAC+1])                     #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24
label('lslw#19')
st([vAC])                       #19
ld([vAC+1])                     #20
adda(AC)                        #21
adda(1)                         #22
jmp(Y,'REENTER_28')             #23
st([vAC+1])                     #24

# POKE implementation
label('poke#14')
adda(1,X)                       #14
ld([X])                         #15
ld(AC,Y)                        #16
ld([vTmp],X)                    #17
ld([X])                         #18
ld(AC,X)                        #19
ld([vAC])                       #20
st([Y,X])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# PEEK implementation
label('peek')
ld([vPC])                       #13
suba(1)                         #14
st([vPC])                       #15
ld([vAC],X)                     #16
ld([vAC+1],Y)                   #17
ld([Y,X])                       #18
st([vAC])                       #19
ld(0)                           #20
st([vAC+1])                     #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# DOKE implementation
label('doke')
adda(1,X)                       #13
ld([X])                         #14
ld(AC,Y)                        #15
ld([vTmp],X)                    #16
ld([X])                         #17
ld(AC,X)                        #18
ld([vAC])                       #19
st([Y,Xpp])                     #20
ld([vAC+1])                     #21
st([Y,X])                       #22 Incompatible with REENTER_28
ld(hi('REENTER'),Y)             #23
jmp(Y,'REENTER')                #24
ld(-28/2)                       #25

# DEEK implementation
label('deek')
ld([vPC])                       #13
suba(1)                         #14
st([vPC])                       #15
ld([vAC],X)                     #16
ld([vAC+1],Y)                   #17
ld([Y,X])                       #18
st([Y,Xpp])                     #19 Just X++
st([vAC])                       #20
ld([Y,X])                       #21
ld(hi('REENTER_28'),Y)          #22
jmp(Y,'REENTER_28')             #23
st([vAC+1])                     #24

# ANDW implementation
label('andw')
st([vTmp])                      #13
adda(1,X)                       #14
ld([X])                         #15
anda([vAC+1])                   #16
st([vAC+1])                     #17
ld([vTmp],X)                    #18
ld([X])                         #19
anda([vAC])                     #20
st([vAC])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# ORW implementation
label('orw')
st([vTmp])                      #13
adda(1,X)                       #14
ld([X])                         #15
ora([vAC+1])                    #16
st([vAC+1])                     #17
ld([vTmp],X)                    #18
ld([X])                         #19
ora([vAC])                      #20
st([vAC])                       #21
label('orw#22')
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24
#
# XORW implementation
label('xorw')
adda(1,X)                       #13
ld([X])                         #14
xora([vAC+1])                   #15
st([vAC+1])                     #16
ld([vTmp],X)                    #17
ld([X])                         #18
xora([vAC])                     #19
bra('orw#22')                   #20
st([vAC])                       #21
#
# SYS implementation
label('.sys#16')
ld([vPC])                       #16
suba(2)                         #17
st([vPC])                       #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24//2)                      #21
#
# CALL implementation
# - Displacing CALL adds 4 cycles.
#   This is less critical when we have CALLI.
label('call#14')
ld([vPC])                       #14
adda(2)                         #15 Point to instruction after CALL
st([vLR])                       #16
ld([vPC+1])                     #17
st([vLR+1])                     #18
ld([X])                         #19
st([vPC+1])                     #20
ld([vTmp],X)                    #21
ld([X])                         #22
suba(2)                         #23 Because NEXT will add 2
st([vPC])                       #24
ld(hi('REENTER'),Y)             #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27



#-----------------------------------------------------------------------
#
#  vCPU extension functions (for acceleration and compaction) follow below.
#
#  The naming convention is: SYS_<CamelCase>[_v<V>]_<N>
#
#  With <N> the maximum number of cycles the function will run
#  (counted from NEXT to NEXT). This is the same number that must
#  be passed to the 'SYS' vCPU instruction as operand, and it will
#  appear in the GCL code upon use.
#
#  If a SYS extension got introduced after ROM v1, the version number of
#  introduction is included in the name. This helps the programmer to be
#  reminded to verify the acutal ROM version and fail gracefully on older
#  ROMs than required. See also Docs/GT1-files.txt on using [romType].
#
#-----------------------------------------------------------------------

fillers(until=0xa7)

#-----------------------------------------------------------------------
# Extension SYS_Random_34: Update entropy and copy to vAC
#-----------------------------------------------------------------------

# This same algorithm runs automatically once per vertical blank.
# Use this function to get numbers at a higher rate.
#
# Variables:
#       vAC

label('SYS_Random_34')
ld([vTicks])                    #15
xora([entropy+1])               #16
ld(1,Y)                         #17
adda([entropy+0])               #18
st([entropy+0])                 #19
st([vAC+0])                     #20
if WITH_128K_BOARD:
  adda([Y,entropy2])            #21
  st([Y,entropy2])              #22
else:
  adda([entropy+2])             #21
  st([entropy+2])               #22
bmi('.sysRnd0')                 #23
bra('.sysRnd1')                 #24
xora(64+16+2+1)                 #25
label('.sysRnd0')
xora(64+32+8+4)                 #25
label('.sysRnd1')
adda([entropy+1])               #26
st([entropy+1])                 #27
st([vAC+1])                     #28
ld(hi('REENTER'),Y)             #29
jmp(Y,'REENTER')                #30
ld(-34/2)                       #31

label('SYS_LSRW7_30')
ld([vAC])                       #15
anda(128,X)                     #16
ld([vAC+1])                     #17
adda(AC)                        #18
ora([X])                        #19
st([vAC])                       #20
ld([vAC+1])                     #21
anda(128,X)                     #22
ld([X])                         #23
st([vAC+1])                     #24
ld(hi('REENTER'),Y)             #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27

label('SYS_LSRW8_24')
ld([vAC+1])                     #15
st([vAC])                       #16
ld(0)                           #17
st([vAC+1])                     #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24/2)                       #21

label('SYS_LSLW8_24')
ld([vAC])                       #15
st([vAC+1])                     #16
ld(0)                           #17
st([vAC])                       #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24/2)                       #21

#-----------------------------------------------------------------------
# Extension SYS_Draw4_30
#-----------------------------------------------------------------------

# Draw 4 pixels on screen, horizontally next to each other
#
# Variables:
#       sysArgs[0:3]    Pixels (in)
#       sysArgs[4:5]    Position on screen (in)

label('SYS_Draw4_30')
ld([sysArgs+4],X)               #15
ld([sysArgs+5],Y)               #16
ld([sysArgs+0])                 #17
st([Y,Xpp])                     #18
ld([sysArgs+1])                 #19
st([Y,Xpp])                     #20
ld([sysArgs+2])                 #21
st([Y,Xpp])                     #22
ld([sysArgs+3])                 #23
st([Y,Xpp])                     #24
ld(hi('REENTER'),Y)             #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27

#-----------------------------------------------------------------------
# Extension SYS_VDrawBits_134:
#-----------------------------------------------------------------------

# Draw slice of a character, 8 pixels vertical
#
# Variables:
#       sysArgs[0]      Color 0 "background" (in)
#       sysArgs[1]      Color 1 "pen" (in)
#       sysArgs[2]      8 bits, highest bit first (in, changed)
#       sysArgs[4:5]    Position on screen (in)

label('SYS_VDrawBits_134')
ld(hi('sys_VDrawBits'),Y)       #15
jmp(Y,'sys_VDrawBits')          #16
ld([sysArgs+4],X)               #17

#-----------------------------------------------------------------------

# Interrupt handler:
#       ... IRQ payload ...
#       LDWI $400
#       LUP  $xx  ==> vRTI
fillers(until=251-16)

# vRTI immediate resume
label('vRTI#32')
ld([vCpuSelect],Y)              #32
ld(-36//2)                      #33
jmp(Y,'ENTER')                  #34
adda([vTicks])                  #35-36=-1

# Immediate resume is possible when there is enough time for
# finishing vrti and executing the next instruction (possibly v6502)
vRtiNeeds=36//2+maxTicks+v6502_adjust

label('vRTI#22')
ld([vIrqSave+2])                #22
st([vAC])                       #23
ld([vIrqSave+3])                #24
st([vAC+1])                     #25
ld([vIrqSave+4])                #26
st([vCpuSelect])                #27
ld([vTicks])                    #28 enough time for immediate resume?
adda(maxTicks-vRtiNeeds)        #29
bge('vRTI#32')                  #30
ld(hi('RESYNC'),Y)              #31
jmp(Y,'RESYNC')                 #32
adda(vRtiNeeds-30//2)           #33-30=3

# Resync cycle adjustment must be positive
assert (maxTicks-vRtiNeeds)+(vRtiNeeds-30//2) >= 0

# vRTI entry point
assert(pc()&255 == 251)         # The landing offset 251 for LUP trampoline is fixed
ld([vIrqSave+0])                #17
st([vPC])                       #18
ld([vIrqSave+1])                #19
bra('vRTI#22')                  #20
st([vPC+1])                     #21


#-----------------------------------------------------------------------
#
#  $0500 ROM page 5-6: Shift table and code
#
#-----------------------------------------------------------------------

align(0x100, size=0x200)

# Lookup table for i>>n, with n in 1..6
# Indexing ix = i & ~b | (b-1), where b = 1<<(n-1)
#       ...
#       ld   <.ret
#       st   [vTmp]
#       ld   >shiftTable,y
#       <calculate ix>
#       jmp  y,ac
#       bra  $ff
# .ret: ...
#
# i >> 7 can be always be done with RAM: [i&128]
#       ...
#       anda $80,x
#       ld   [x]
#       ...

label('shiftTable')
shiftTable = pc()

for ix in range(255):
  for n in range(1,7): # Find first zero
    if ~ix & (1 << (n-1)):
      break
  pattern = ['x' if i<n else '1' if ix&(1<<i) else '0' for i in range(8)]
  ld(ix>>n); C('0b%s >> %d' % (''.join(reversed(pattern)), n))

assert pc()&255 == 255
bra([vTmp])                     # Jumps back into next page

label('SYS_LSRW1_48')
assert pc()&255 == 0            # First instruction on this page *must* be a nop
nop()                           #15
ld(hi('shiftTable'),Y)          #16 Logical shift right 1 bit (X >> 1)
ld('.sysLsrw1a')                #17 Shift low byte
st([vTmp])                      #18
ld([vAC])                       #19
anda(0b11111110)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw1a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8
anda(1)                         #28
adda(127)                       #29
anda(128)                       #30
ora([vAC])                      #31
st([vAC])                       #32
ld('.sysLsrw1b')                #33 Shift high byte
st([vTmp])                      #34
ld([vAC+1])                     #35
anda(0b11111110)                #36
jmp(Y,AC)                       #37
bra(255)                        #38 bra shiftTable+255
label('.sysLsrw1b')
st([vAC+1])                     #42
ld(hi('REENTER'),Y)             #43
jmp(Y,'REENTER')                #44
ld(-48/2)                       #45

label('SYS_LSRW2_52')
ld(hi('shiftTable'),Y)          #15 Logical shift right 2 bit (X >> 2)
ld('.sysLsrw2a')                #16 Shift low byte
st([vTmp])                      #17
ld([vAC])                       #18
anda(0b11111100)                #19
ora( 0b00000001)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw2a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8:9
adda(AC)                        #28
adda(AC)                        #29
adda(AC)                        #30
adda(AC)                        #31
adda(AC)                        #32
adda(AC)                        #33
ora([vAC])                      #34
st([vAC])                       #35
ld('.sysLsrw2b')                #36 Shift high byte
st([vTmp])                      #37
ld([vAC+1])                     #38
anda(0b11111100)                #39
ora( 0b00000001)                #40
jmp(Y,AC)                       #41
bra(255)                        #42 bra shiftTable+255
label('.sysLsrw2b')
st([vAC+1])                     #46
ld(hi('REENTER'),Y)             #47
jmp(Y,'REENTER')                #48
ld(-52/2)                       #49

label('SYS_LSRW3_52')
ld(hi('shiftTable'),Y)          #15 Logical shift right 3 bit (X >> 3)
ld('.sysLsrw3a')                #16 Shift low byte
st([vTmp])                      #17
ld([vAC])                       #18
anda(0b11111000)                #19
ora( 0b00000011)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw3a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8:10
adda(AC)                        #28
adda(AC)                        #29
adda(AC)                        #30
adda(AC)                        #31
adda(AC)                        #32
ora([vAC])                      #33
st([vAC])                       #34
ld('.sysLsrw3b')                #35 Shift high byte
st([vTmp])                      #36
ld([vAC+1])                     #37
anda(0b11111000)                #38
ora( 0b00000011)                #39
jmp(Y,AC)                       #40
bra(255)                        #41 bra shiftTable+255
label('.sysLsrw3b')
st([vAC+1])                     #45
ld(-52/2)                       #46
ld(hi('REENTER'),Y)             #47
jmp(Y,'REENTER')                #48
#nop()                          #49

label('SYS_LSRW4_50')
ld(hi('shiftTable'),Y)          #15,49 Logical shift right 4 bit (X >> 4)
ld('.sysLsrw4a')                #16 Shift low byte
st([vTmp])                      #17
ld([vAC])                       #18
anda(0b11110000)                #19
ora( 0b00000111)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw4a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8:11
adda(AC)                        #28
adda(AC)                        #29
adda(AC)                        #30
adda(AC)                        #31
ora([vAC])                      #32
st([vAC])                       #33
ld('.sysLsrw4b')                #34 Shift high byte'
st([vTmp])                      #35
ld([vAC+1])                     #36
anda(0b11110000)                #37
ora( 0b00000111)                #38
jmp(Y,AC)                       #39
bra(255)                        #40 bra shiftTable+255
label('.sysLsrw4b')
st([vAC+1])                     #44
ld(hi('REENTER'),Y)             #45
jmp(Y,'REENTER')                #46
ld(-50/2)                       #47

label('SYS_LSRW5_50')
ld(hi('shiftTable'),Y)          #15 Logical shift right 5 bit (X >> 5)
ld('.sysLsrw5a')                #16 Shift low byte
st([vTmp])                      #17
ld([vAC])                       #18
anda(0b11100000)                #19
ora( 0b00001111)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw5a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8:13
adda(AC)                        #28
adda(AC)                        #29
adda(AC)                        #30
ora([vAC])                      #31
st([vAC])                       #32
ld('.sysLsrw5b')                #33 Shift high byte
st([vTmp])                      #34
ld([vAC+1])                     #35
anda(0b11100000)                #36
ora( 0b00001111)                #37
jmp(Y,AC)                       #38
bra(255)                        #39 bra shiftTable+255
label('.sysLsrw5b')
st([vAC+1])                     #44
ld(-50/2)                       #45
ld(hi('REENTER'),Y)             #46
jmp(Y,'REENTER')                #47
#nop()                          #48

label('SYS_LSRW6_48')
ld(hi('shiftTable'),Y)          #15,44 Logical shift right 6 bit (X >> 6)
ld('.sysLsrw6a')                #16 Shift low byte
st([vTmp])                      #17
ld([vAC])                       #18
anda(0b11000000)                #19
ora( 0b00011111)                #20
jmp(Y,AC)                       #21
bra(255)                        #22 bra shiftTable+255
label('.sysLsrw6a')
st([vAC])                       #26
ld([vAC+1])                     #27 Transfer bit 8:13
adda(AC)                        #28
adda(AC)                        #29
ora([vAC])                      #30
st([vAC])                       #31
ld('.sysLsrw6b')                #32 Shift high byte
st([vTmp])                      #33
ld([vAC+1])                     #34
anda(0b11000000)                #35
ora( 0b00011111)                #36
jmp(Y,AC)                       #37
bra(255)                        #38 bra shiftTable+255
label('.sysLsrw6b')
st([vAC+1])                     #42
ld(hi('REENTER'),Y)             #43
jmp(Y,'REENTER')                #44
ld(-48/2)                       #45

label('SYS_LSLW4_46')
ld(hi('shiftTable'),Y)          #15 Logical shift left 4 bit (X << 4)
ld('.sysLsrl4')                 #16
st([vTmp])                      #17
ld([vAC+1])                     #18
adda(AC)                        #19
adda(AC)                        #20
adda(AC)                        #21
adda(AC)                        #22
st([vAC+1])                     #23
ld([vAC])                       #24
anda(0b11110000)                #25
ora( 0b00000111)                #26
jmp(Y,AC)                       #27
bra(255)                        #28 bra shiftTable+255
label('.sysLsrl4')
ora([vAC+1])                    #32
st([vAC+1])                     #33
ld([vAC])                       #34
adda(AC)                        #35
adda(AC)                        #36
adda(AC)                        #37
adda(AC)                        #38
st([vAC])                       #39
ld(-46/2)                       #40
ld(hi('REENTER'),Y)             #41
jmp(Y,'REENTER')                #42
#nop()                          #43

#-----------------------------------------------------------------------
# Extension SYS_Read3_40
#-----------------------------------------------------------------------

# Read 3 consecutive bytes from ROM
#
# Note: This function a bit obsolete, as it has very limited use. It's
#       effectively an application-specific SYS function for the Pictures
#       application from ROM v1. It requires the ROM data be organized
#       with trampoline3a and trampoline3b fragments, and their address
#       in ROM to be known. Better avoid using this.
# Variables:
#       sysArgs[0:2]    Bytes (out)
#       sysArgs[6:7]    ROM pointer (in)

fillers(until = 0xb9)
assert pc() == 0x6b9

label('SYS_Read3_40')
ld([sysArgs+7],Y)               #15,43
jmp(Y,128-7)                    #16 trampoline3a
ld([sysArgs+6])                 #17
label('txReturn')
st([sysArgs+2])                 #34
ld(hi('REENTER'),Y)             #35
jmp(Y,'REENTER')                #36
ld(-40/2)                       #37

def trampoline3a():
  """Read 3 bytes from ROM page"""
  while pc()&255 < 128-7:
    nop()
  bra(AC)                       #18
  C('Trampoline for page $%02x00 reading (entry)' % (pc()>>8))
  bra(123)                      #19
  st([sysArgs+0])               #21
  ld([sysArgs+6])               #22
  adda(1)                       #23
  bra(AC)                       #24
  bra(250)                      #25 trampoline3b
  align(1, size=0x80)

def trampoline3b():
  """Read 3 bytes from ROM page (continue)"""
  while pc()&255 < 256-6:
    nop()
  st([sysArgs+1])               #27
  C('Trampoline for page $%02x00 reading (continue)' % (pc()>>8))
  ld([sysArgs+6])               #28
  adda(2)                       #29
  ld(hi('txReturn'),Y)          #30
  bra(AC)                       #31
  jmp(Y,'txReturn')             #32
  align(1, size=0x100)

#-----------------------------------------------------------------------
# Extension SYS_Unpack_56
#-----------------------------------------------------------------------

# Unpack 3 bytes into 4 pixels
#
# Variables:
#       sysArgs[0:2]    Packed bytes (in)
#       sysArgs[0:3]    Pixels (out)

fillers(until = 0xc0)
assert pc() == 0x6c0
label('SYS_Unpack_56')
ld(hi('unpack#18'),Y)           #15
jmp(Y,'unpack#18')              #16
ld([vTicks])                    #17


#-----------------------------------------------------------------------
#       v6502 right shift instruction
#-----------------------------------------------------------------------

label('v6502_lsr#28')
ld([v6502_ADH],Y)               #28 Result
st([Y,X])                       #29
st([v6502_Qz])                  #30 Z flag
st([v6502_Qn])                  #31 N flag
ld(hi('v6502_next'),Y)          #32
ld(-36/2)                       #33
jmp(Y,'v6502_next')             #34
#nop()                          #35 Overlap
#
label('v6502_ror#36')
ld([v6502_ADH],Y)               #36,38 Result
ora([v6502_BI])                 #37 Transfer bit 8
st([Y,X])                       #38
st([v6502_Qz])                  #39 Z flag
st([v6502_Qn])                  #40 N flag
ld(hi('v6502_next'),Y)          #41
jmp(Y,'v6502_next')             #42
ld(-44/2)                       #43

#-----------------------------------------------------------------------
# Relays for vCPU right shift instructions
#-----------------------------------------------------------------------

label('rorx#25')
ora([vAC+1])                    #29
st([X])                         #30
ld(hi('FSM1C_NEXT'),Y)          #31
jmp(Y,'NEXT')                   #32
ld(-30/2)                       #33

label('rorx#29')
ora([vAC+1])                    #29
st([X])                         #30
ld(hi('FSM1C_NEXT'),Y)          #31
jmp(Y,'NEXT')                   #32
ld(-34/2)                       #33

label('rorx#31')
ora([vAC+1])                    #31
st([X])                         #32
ld(hi('FSM1C_NEXT'),Y)          #33
jmp(Y,'NEXT')                   #34
ld(-36/2)                       #35

label('fsmLSR4#19')
st([vAC])                       #19
ld([vCpuSelect])                #20
adda(1,Y)                       #21
jmp(Y,'NEXT')                   #22
ld(-24/2)                       #23

# Free space to be used for more right shift ops

#-----------------------------------------------------------------------
#
#  $0700 ROM page 7-8: Gigatron font data
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

label('font32up')
for ch in range(32, 32+50):
  comment = 'Char %s' % repr(chr(ch))
  for byte in font.font[ch-32]:
    ld(byte)
    comment = C(comment)

trampoline()

#-----------------------------------------------------------------------

align(0x100, size=0x100)

label('font82up')
for ch in range(32+50, 132):
  comment = 'Char %s' % repr(chr(ch))
  for byte in font.font[ch-32]:
    ld(byte)
    comment = C(comment)

trampoline()

#-----------------------------------------------------------------------
#
#  $0900 ROM page 9: Key table for music
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)
notes = 'CCDDEFFGGAAB'
sampleRate = cpuClock / 200.0 / 4
label('notesTable')
ld(0)
ld(0)
for i in range(0, 250, 2):
  j = i//2-1
  freq = 440.0*2.0**((j-57)/12.0)
  if j>=0 and freq <= sampleRate/2.0:
    key = int(round(32768 * freq / sampleRate))
    octave, note = j//12, notes[j%12]
    sharp = '-' if notes[j%12-1] != note else '#'
    comment = '%s%s%s (%0.1f Hz)' % (note, sharp, octave, freq)
    ld(key&127); C(comment); ld(key>>7)

trampoline()

#-----------------------------------------------------------------------
#
#  $0a00 ROM page 10: Inversion table
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)
label('invTable')

# Unit 64, table offset 16 (=1/4), value offset 1: (x+16)*(y+1) == 64*64 - e
for i in range(251):
  ld(4096//(i+16)-1)

trampoline()

#-----------------------------------------------------------------------
#
#  $0d00 ROM page 11: More SYS functions
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

#-----------------------------------------------------------------------
# Extension SYS_SetMode_v2_80
#-----------------------------------------------------------------------

# Set video mode to 0 to 3 black scanlines per pixel line.
#
# Mainly for making the MODE command available in Tiny BASIC, so that
# the user can experiment. It's adviced to refrain from using
# SYS_SetMode_v2_80 in regular applications. Video mode is a deeply
# personal preference, and the programmer shouldn't overrule the user
# in that choice. The Gigatron philisophy is that the end user has
# the final say on what happens on the system, not the application,
# even if that implies a degraded performance. This doesn't mean that
# all applications must work well in all video modes: mode 1 is still
# the default. If an application really doesn't work at all in that
# mode, it's acceptable to change mode once after loading.
#
# There's no "SYS_GetMode" function.
#
# Variables:
#       vAC bit 0:1     Mode:
#                         0      "ABCD" -> Full mode (slowest)
#                         1      "ABC-" -> Default mode after reset
#                         2      "A-C-" -> at67's mode
#                         3      "A---" -> HGM's mode
#       vAC bit 2:15    Ignored bits and should be 0
#
# Special values (ROM v4):
#       vAC = 1975      Zombie mode (no video signals, no input,
#                        no blinkenlights).
#       vAC = -1        Leave zombie mode and restore previous mode.

# Actual duration is <80 cycles, but keep some room for future extensions
label('SYS_SetMode_v2_80')
ld(hi('sys_SetMode'),Y)         #15
jmp(Y,'sys_SetMode')            #16
ld([vReturn])                   #17

#-----------------------------------------------------------------------
# Extension SYS_SetMemory_v2_54
#-----------------------------------------------------------------------

# SYS function for setting 1..256 bytes
#
# sysArgs[0]   Copy count (in, changed)
# sysArgs[1]   Copy value (in)
# sysArgs[2:3] Destination address (in, changed)
#
# Sets up to 8 bytes per invocation before restarting itself through vCPU.
# Doesn't wrap around page boundary. Can run 3 times per 148-cycle time slice.
# All combined that gives a 300% speedup over ROMv4 and before.

label('SYS_SetMemory_v2_54')
ld([sysArgs+0])                 #15
bra('sys_SetMemory#18')         #16
ld([sysArgs+2],X)               #17

#-----------------------------------------------------------------------
# Extension SYS_SendSerial1_v3_80
#-----------------------------------------------------------------------

# SYS function for sending data over serial controller port using
# pulse width modulation of the vertical sync signal.
#
# Variables:
#       sysArgs[0:1]    Source address               (in, changed)
#       sysArgs[2]      Start bit mask (typically 1) (in, changed)
#       sysArgs[3]      Number of send frames X      (in, changed)
#
# The sending will abort if input data is detected on the serial port.
# Returns 0 in case of all bits sent, or <>0 in case of abort
#
# This modulates the next upcoming X vertical pulses with the supplied
# data. A zero becomes a 7 line vPulse, a one will be 9 lines.
# After that, the vPulse width falls back to 8 lines (idle).

label('SYS_SendSerial1_v3_80')
ld([videoY])                    #15
bra('sys_SendSerial1')          #16
xora(videoYline0)               #17 First line of vertical blank

#-----------------------------------------------------------------------
# Extension SYS_ExpanderControl_v4_40
#-----------------------------------------------------------------------

# Sets the I/O and RAM expander's control register
#
# Variables:
#       vAC bit 2       Device enable /SS0
#           bit 3       Device enable /SS1
#           bit 4       Device enable /SS2
#           bit 5       Device enable /SS3
#           bit 6       Banking B0
#           bit 7       Banking B1
#           bit 15      Data out MOSI
#       sysArgs[7]      Cache for control state (written to)
#
# Intended for prototyping, and probably too low-level for most applications
# Still there's a safeguard: it's not possible to disable RAM using this

label('SYS_ExpanderControl_v4_40')
ld(hi('sys_ExpanderControl'),Y) #15
jmp(Y,'sys_ExpanderControl')    #16
ld(0b00001100)                  #17
#    ^^^^^^^^
#    |||||||`-- SCLK
#    ||||||`--- Not connected
#    |||||`---- /SS0
#    ||||`----- /SS1
#    |||`------ /SS2 or /CPOL
#    ||`------- /SS3 or /ZPBANK
#    |`-------- B0
#    `--------- B1

#-----------------------------------------------------------------------
# Extension SYS_Run6502_v4_80
#-----------------------------------------------------------------------

# Transfer control to v6502
#
# Calling 6502 code from vCPU goes (only) through this SYS function.
# Directly modifying the vCpuSelect variable is unreliable. The
# control transfer is immediate, without waiting for the current
# time slice to end or first returning to vCPU.
#
# vCPU code and v6502 code can interoperate without much hassle:
# - The v6502 program counter is vLR, and v6502 doesn't touch vPC
# - Returning to vCPU is with the BRK instruction
# - BRK doesn't dump process state on the stack
# - vCPU can save/restore the vLR with PUSH/POP
# - Stacks are shared, vAC is shared
# - vAC can indicate what the v6502 code wants. vAC+1 will be cleared
# - Alternative is to leave a word in sysArgs[6:7] (v6502 X and Y registers)
# - Another way is to set vPC before BRK, and vCPU will continue there(+2)
#
# Calling v6502 code from vCPU looks like this:
#       LDWI  SYS_Run6502_v4_80
#       STW   sysFn
#       LDWI  $6502_start_address
#       STW   vLR
#       SYS   80
#
# Variables:
#       vAC             Accumulator
#       vLR             Program Counter
#       vSP             Stack Pointer (+1)
#       sysArgs[6]      Index Register X
#       sysArgs[7]      Index Register Y
# For info:
#       sysArgs[0:1]    Address Register, free to clobber
#       sysArgs[2]      Instruction Register, free to clobber
#       sysArgs[3:5]    Flags, don't touch
#
# Implementation details::
#
#  The time to reserve for this transition is the maximum time
#  between NEXT and v6502_check. This is
#       SYS call duration + 2*v6502_maxTicks + (v6502_overhead - vCPU_overhead)
#     = 22 + 28 + (11 - 9) = 62 cycles.
#  So reserving 80 cycles is future proof. This isn't overhead, as it includes
#  the fetching of the first 6502 opcode and its operands..
#
#                      0            10                 28=0         9
#    ---+----+---------+------------+------------------+-----------+---
# video | nop| runVcpu |   ENTER    | At least one ins |   EXIT    | video
#    ---+----+---------+------------+------------------+-----------+---
#        sync  prelude  ENTER-to-ins    ins-to-NEXT     NEXT-to-video
#       |<-->|
#        0/1 |<------->|
#                 5    |<----------------------------->|
#          runVCpu_overhead           28               |<--------->|
#                                 2*maxTicks                 9
#                                                      vCPU_overhead
#
#                      0                21                    38=0       11
#    ---+----+---------+----------------+--------------------+-----------+---
# video | nop| runVcpu |   v6502_ENTER  | At least one fetch |v6502_exitB| video
#    ---+----+---------+----------------+--------------------+-----------+---
#        sync  prelude   enter-to-fetch     fetch-to-check    check-to-video
#       |<-->|
#        0/1 |<------->|
#                 5    |<----------------------------------->|
#          runVcpu_overhead           38                     |<--------->|
#                              2*v6520_maxTicks                    11
#                                                            v6502_overhead

label('SYS_Run6502_v4_80')
ld(hi('sys_v6502'),Y)           #15
jmp(Y,'sys_v6502')              #16
ld(hi('v6502_ENTER'))           #17 Activate v6502

#-----------------------------------------------------------------------
# Extension SYS_ResetWaveforms_v4_50
#-----------------------------------------------------------------------

# soundTable[4x+0] = sawtooth, to be modified into metallic/noise
# soundTable[4x+1] = pulse
# soundTable[4x+2] = triangle
# soundTable[4x+3] = sawtooth, also useful to right shift 2 bits

label('SYS_ResetWaveforms_v4_50')
ld(hi('sys_ResetWaveforms'),Y)  #15 Initial setup of waveforms. [vAC+0]=i
jmp(Y,'sys_ResetWaveforms')     #16
ld(soundTable>>8,Y)             #17

#-----------------------------------------------------------------------
# Extension SYS_ShuffleNoise_v4_46
#-----------------------------------------------------------------------

# Use simple 6-bits variation of RC4 to permutate waveform 0 in soundTable

label('SYS_ShuffleNoise_v4_46')
ld(hi('sys_ShuffleNoise'),Y)    #15 Shuffle soundTable[4i+0]. [vAC+0]=4j, [vAC+1]=4i
jmp(Y,'sys_ShuffleNoise')       #16
ld(soundTable>>8,Y)             #17

#-----------------------------------------------------------------------
# Extension SYS_SpiExchangeBytes_v4_134
#-----------------------------------------------------------------------

# Send AND receive 1..256 bytes over SPI interface

# Variables:
#       sysArgs[0]      Page index start, for both send/receive (in, changed)
#       sysArgs[1]      Memory page for send data (in)
#       sysArgs[2]      Page index stop (in)
#       sysArgs[3]      Memory page for receive data (in)
#       sysArgs[4]      Scratch (changed)

label('SYS_SpiExchangeBytes_v4_134')
ld(hi('sys_SpiExchangeBytes'),Y)#15
jmp(Y,'sys_SpiExchangeBytes')   #16
ld(hi(ctrlBits),Y)              #17 Control state as saved by SYS_ExpanderControl


#-----------------------------------------------------------------------
# Extension SYS_ReceiveSerial1_v6_32
#-----------------------------------------------------------------------

# SYS function for receiving one byte over the serial controller port.
# This is a public version of SYS_NextByteIn from the loader private
# extension.  A byte is read from IN when videoY reaches
# sysArgs[3]. The byte is added to the checksum sysArgs[2] then stored
# at address sysArgs[0:1] which gets incremented.
#
# The 65 bytes of a serial frame can be read for the following values
# of videoY: 207 (protocol byte) 219 (length, 6 bits only) 235, 251
# (address) then 2, 6, 10, .. 238 stepping by four, then 185.
#
# Variables:
#     sysArgs[0:1] Address
#     sysArgs[2]   Checksum
#     sysArgs[3]   Wait value (videoY)

label('SYS_ReceiveSerial1_v6_32')
bra('sys_ReceiveSerial1')       #15
ld([sysArgs+3])                 #16

#-----------------------------------------------------------------------
#  Implementations
#-----------------------------------------------------------------------

# SYS_SetMemory_54 implementation
label('sys_SetMemory#18')
ld([sysArgs+3],Y)               #18
ble('.sysSb#21')                #19 Enter fast lane if >=128 or at 0 (-> 256)
suba(8)                         #20
bge('.sysSb#23')                #21 Or when >=8
st([sysArgs+0])                 #22
anda(4)                         #23
beq('.sysSb#26')                #24
ld([sysArgs+1])                 #25 Set 4 pixels
st([Y,Xpp])                     #26
st([Y,Xpp])                     #27
st([Y,Xpp])                     #28
bra('.sysSb#31')                #29
st([Y,Xpp])                     #30
label('.sysSb#26')
wait(31-26)                     #26
label('.sysSb#31')
ld([sysArgs+0])                 #31
anda(2)                         #32
beq('.sysSb#35')                #33
ld([sysArgs+1])                 #34 Set 2 pixels
st([Y,Xpp])                     #35
bra('.sysSb#38')                #36
st([Y,Xpp])                     #37
label('.sysSb#35')
wait(38-35)                     #35
label('.sysSb#38')
ld([sysArgs+0])                 #38
anda(1)                         #39
beq(pc()+3)                     #40
bra(pc()+3)                     #41
ld([sysArgs+1])                 #42 Set 1 pixel
ld([Y,X])                       #42(!) No change
st([Y,X])                       #43
ld(hi('NEXTY'),Y)               #44 Return
jmp(Y,'NEXTY')                  #45 All done
ld(-48/2)                       #46
label('.sysSb#21')
nop()                           #21
st([sysArgs+0])                 #22
label('.sysSb#23')
ld([sysArgs+1])                 #23 Set 8 pixels
st([Y,Xpp])                     #24
st([Y,Xpp])                     #25
st([Y,Xpp])                     #26
st([Y,Xpp])                     #27
st([Y,Xpp])                     #28
st([Y,Xpp])                     #29
st([Y,Xpp])                     #30
st([Y,Xpp])                     #31
ld([sysArgs+2])                 #32 Advance write pointer
adda(8)                         #33
st([sysArgs+2],X)               #34 Also X for self-restart
ld([sysArgs+0])                 #35
bne('.sysSb#38f')               #36
ld(hi('REENTER'),Y)             #37 Done.
jmp(Y,'REENTER')                #38
ld(-42/2)                       #39
label('.sysSb#38f')
ld(-26/2)                       #38 Not yet done.
adda([vTicks])                  #13 = 39 - 26
st([vTicks])                    #14
adda(min(0,maxTicks-(26+26)/2)) #15
bge('sys_SetMemory#18')         #16 Self-dispatch when enough time
ld([sysArgs+0])                 #17 AC and X as expected
ld(-2)                          #18 Self-restart otherwise
adda([vPC])                     #19
st([vPC])                       #20
ld(hi('REENTER'),Y)             #21
jmp(Y,'REENTER')                #22
ld(-26/2)                       #23

# SYS_SetMode_80 implementation
label('sys_SetMode')
bne(pc()+3)                     #18
bra(pc()+2)                     #19
ld('startVideo')                #20 First enable video if disabled
st([vReturn])                   #20,21
ld([vAC+1])                     #22
beq('.sysSm#25')                #23
ld(hi('REENTER'),Y)             #24
xora([vAC])                     #25
xora((1975>>8)^(1975&255))      #26 Poor man\'s 1975 detection
bne(pc()+3)                     #27
bra(pc()+3)                     #28
assert videoZ == 0x0100
st([vReturn])                   #29 DISABLE video/audio/serial/etc
nop()                           #29(!) Ignore and return
jmp(Y,'REENTER')                #30
ld(-34/2)                       #31
label('.sysSm#25')
ld([vAC])                       #25 Mode 0,1,2,3
anda(3)                         #26
adda('.sysSm#30')               #27
bra(AC)                         #28
bra('.sysSm#31')                #29
label('.sysSm#30')
ld('pixels')                    #30 videoB lines
ld('pixels')                    #30
ld('nopixels')                  #30
ld('nopixels')                  #30
label('.sysSm#31')
st([videoModeB])                #31
ld([vAC])                       #32
anda(3)                         #33
adda('.sysSm#37')               #34
bra(AC)                         #35
bra('.sysSm#38')                #36
label('.sysSm#37')
ld('pixels')                    #37 videoC lines
ld('pixels')                    #37
ld('pixels')                    #37
ld('nopixels')                  #37
label('.sysSm#38')
if WITH_512K_BOARD:
  nop()                           #38
else:
  st([videoModeC])                #38
ld([vAC])                       #39
anda(3)                         #40
adda('.sysSm#44')               #41
bra(AC)                         #42
bra('.sysSm#45')                #43
label('.sysSm#44')
ld('pixels')                    #44 videoD lines
ld('nopixels')                  #44
ld('nopixels')                  #44
ld('nopixels')                  #44
label('.sysSm#45')
st([videoModeD])                #45
jmp(Y,'REENTER')                #46
ld(-50/2)                       #47

# SYS_SendSerial1_v3_80 implementation
label('sys_SendSerial1')
beq('.sysSs#20')                #18
ld([sysArgs+0],X)               #19
ld([vPC])                       #20 Wait for vBlank
suba(2)                         #21
ld(hi('REENTER_28'),Y)          #22
jmp(Y,'REENTER_28')             #23
st([vPC])                       #24
label('.sysSs#20')
ld([sysArgs+1],Y)               #20 Synchronized with vBlank
ld([Y,X])                       #21 Copy next bit
anda([sysArgs+2])               #22
bne(pc()+3)                     #23
bra(pc()+3)                     #24
ld(7*2)                         #25
ld(9*2)                         #25
st([videoPulse])                #26
ld([sysArgs+2])                 #27 Rotate input bit
adda(AC)                        #28
bne(pc()+3)                     #29
bra(pc()+2)                     #30
ld(1)                           #31
st([sysArgs+2])                 #31,32 (must be idempotent)
anda(1)                         #33 Optionally increment pointer
adda([sysArgs+0])               #34
st([sysArgs+0],X)               #35
ld([sysArgs+3])                 #36 Frame counter
suba(1)                         #37
beq('.sysSs#40')                #38
ld(hi('REENTER'),Y)             #39
st([sysArgs+3])                 #40
ld([serialRaw])                 #41 Test for anything being sent back
xora(255)                       #42
beq('.sysSs#45')                #43
st([vAC])                       #44 Abort after key press with non-zero error
st([vAC+1])                     #45
jmp(Y,'REENTER')                #46
ld(-50/2)                       #47
label('.sysSs#45')
ld([vPC])                       #45 Continue sending bits
suba(2)                         #46
st([vPC])                       #47
jmp(Y,'REENTER')                #48
ld(-52/2)                       #49
label('.sysSs#40')
st([vAC])                       #40 Stop sending bits, no error
st([vAC+1])                     #41
jmp(Y,'REENTER')                #42
ld(-46/2)                       #43

# SYS_ReceiveSerialByte implementation
label('sys_ReceiveSerial1')
xora([videoY])                  #17
bne('.sysRsb#20')               #18
ld([sysArgs+0],X)               #19
ld([sysArgs+1],Y)               #20
ld(IN)                          #21
st([Y,X])                       #22
adda([sysArgs+2])               #23
st([sysArgs+2])                 #24
ld([sysArgs+0])                 #25
adda(1)                         #26
st([sysArgs+0])                 #27
ld(hi('NEXTY'),Y)               #28
jmp(Y,'NEXTY')                  #29
ld(-32/2)                       #30
# Restart the instruction in the next timeslice
label('.sysRsb#20')
ld([vPC])                       #20
suba(2)                         #21
ld(hi('REENTER_28'),Y)          #22
jmp(Y,'REENTER_28')             #23
st([vPC])                       #24

# CALLI implementation (vCPU instruction)
label('calli#13')
adda(3)                         #13,43
st([vLR])                       #14
ld([vPC+1])                     #15
st([vLR+1],Y)                   #16
ld([Y,X])                       #17
st([Y,Xpp])                     #18 Just X++
suba(2)                         #19
st([vPC])                       #20
ld([Y,X])                       #21
ld(hi('REENTER_28'),Y)          #22
jmp(Y,'REENTER_28')             #23
st([vPC+1])                     #24

# -------------------------------------------------------------
# vCPU instructions for comparisons between two 16-bit operands
# -------------------------------------------------------------
#
# vCPU's conditional branching (BCC) always compares vAC against 0,
# treating vAC as a two's complement 16-bit number. When we need to
# compare two arbitrary numnbers we normally first take their difference
# with SUBW.  However, when this difference is too large, the subtraction
# overflows and we get the wrong outcome. To get it right over the
# entire range, an elaborate sequence is needed. TinyBASIC uses this
# blurp for its relational operators. (It compares stack variable $02
# with zero page variable $3a.)
#
#       0461  ee 02            LDLW  $02
#       0463  fc 3a            XORW  $3a
#       0465  35 53 6a         BGE   $046c
#       0468  ee 02            LDLW  $02
#       046a  90 6e            BRA   $0470
#       046c  ee 02            LDLW  $02
#       046e  b8 3a            SUBW  $3a
#       0470  35 56 73         BLE   $0475
#
# The CMPHS and CMPHU instructions were introduced to simplify this.
# They inspect both operands to see if there is an overflow risk. If
# so, they modify vAC such that their difference gets smaller, while
# preserving the relation between the two operands. After that, the
# SUBW instruction can't overflow and we achieve a correct comparison.
# Use CMPHS for signed comparisons and CMPHU for unsigned. With these,
# the sequence above becomes:
#
#       0461  ee 02            LDLW  $02
#       0463  1f 3b            CMPHS $3b        Note: high byte of operand
#       0465  b8 3a            SUBW  $3a
#       0467  35 56 73         BLE   $0475
#
# CMPHS/CMPHU don't make much sense other than in combination with
# SUBW. These modify vACH, if needed, as given in the following table:
#
#       vACH  varH  |     vACH
#       bit7  bit7  | CMPHS  CMPHU
#       ---------------------------
#         0     0   |  vACH   vACH      no change needed
#         0     1   | varH+1 varH-1     narrowing the range
#         1     0   | varH-1 varH+1     narrowing the range
#         1     1   |  vACH   vACH      no change needed
#       ---------------------------


# CMPHS implementation (vCPU instruction)
label('cmphs#13')
ld([vAC+1])                     #13
xora([X])                       #14
bpl('cmphu#17')                 #15
ld(hi('NEXTY'),Y)               #16
ld([X])                         #17
bmi(pc()+3)                     #18
bra(pc()+3)                     #19
suba(1)                         #20
adda(1)                         #20
st([vAC+1])                     #21
jmp(Y,'REENTER')                #22
ld(-26/2)                       #23

# CMPHU implementation (vCPU instruction)
label('cmphu#13')
ld([vAC+1])                     #13
xora([X])                       #14
bpl('cmphu#17')                 #15
ld(hi('NEXTY'),Y)               #16
ld([X])                         #17
bmi(pc()+3)                     #18
bra(pc()+3)                     #19
adda(1)                         #20
suba(1)                         #20
st([vAC+1])                     #21
jmp(Y,'REENTER')                #22
ld(-26/2)                       #23

# No-operation for CMPHS/CMPHU when high bits are equal
label('cmphu#17')
jmp(Y,'NEXTY')                  #17
ld(-20/2)                       #18

# PEEKA implementation
label('peeka#13')
st([vTmp])                      #13
ld([vAC+1],Y)                   #14
ld([vAC],X)                     #15
ld([Y,X])                       #16
ld([vTmp],X)                    #17
st([X])                         #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24//2)                      #21


#-----------------------------------------------------------------------
#
#  $0c00 ROM page 12: More SYS functions (sprites)
#
#       Page 1: vertical blank interval
#       Page 2: visible scanlines
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

#-----------------------------------------------------------------------
# Extension SYS_Sprite6_v3_64
# Extension SYS_Sprite6x_v3_64
# Extension SYS_Sprite6y_v3_64
# Extension SYS_Sprite6xy_v3_64
#-----------------------------------------------------------------------

# Blit sprite in screen memory
#
# Variables
#       vAC             Destination address in screen
#       sysArgs[0:1]    Source address of 6xY pixels (colors 0..63) terminated
#                       by negative byte value N (typically N = -Y)
#       sysArgs[2:7]    Scratch (user as copy buffer)
#
# This SYS function draws a sprite of 6 pixels wide and Y pixels high.
# The pixel data is read sequentually from RAM, in horizontal chunks
# of 6 pixels at a time, and then written to the screen through the
# destination pointer (each chunk underneath the previous), thus
# drawing a 6xY stripe. Pixel values should be non-negative. The first
# negative byte N after a chunk signals the end of the sprite data.
# So the sprite's height Y is determined by the source data and is
# therefore flexible. This negative byte value, typically N == -Y,
# is then used to adjust the destination pointer's high byte, to make
# it easier to draw sprites wider than 6 pixels: just repeat the SYS
# call for as many 6-pixel wide stripes you need. All arguments are
# already left in place to facilitate this. After one call, the source
# pointer will point past that source data, effectively:
#       src += Y * 6 + 1
# The destination pointer will have been adjusted as:
#       dst += (Y + N) * 256 + 6
# (With arithmetic wrapping around on the same memory page)
#
# Y is only limited by source memory, not by CPU cycles. The
# implementation is such that the SYS function self-repeats, each
# time drawing the next 6-pixel chunk. It can typically draw 12
# pixels per scanline this way.

label('SYS_Sprite6_v3_64')

ld([sysArgs+0],X)               #15 Pixel data source address
ld([sysArgs+1],Y)               #16
ld([Y,X])                       #17 Next pixel or stop
bpl('.sysDpx0')                 #18
st([Y,Xpp])                     #19 Just X++

adda([vAC+1])                   #20 Adjust dst for convenience
st([vAC+1])                     #21
ld([vAC])                       #22
adda(6)                         #23
st([vAC])                       #24
ld([sysArgs+0])                 #25 Adjust src for convenience
adda(1)                         #26
st([sysArgs+0])                 #27
nop()                           #28
ld(hi('REENTER'),Y)             #29 Normal exit (no self-repeat)
jmp(Y,'REENTER')                #30
ld(-34/2)                       #31

label('.sysDpx0')
st([sysArgs+2])                 #20 Gobble 6 pixels into buffer
ld([Y,X])                       #21
st([Y,Xpp])                     #22 Just X++
st([sysArgs+3])                 #23
ld([Y,X])                       #24
st([Y,Xpp])                     #25 Just X++
st([sysArgs+4])                 #26
ld([Y,X])                       #27
st([Y,Xpp])                     #28 Just X++
st([sysArgs+5])                 #29
ld([Y,X])                       #30
st([Y,Xpp])                     #31 Just X++
st([sysArgs+6])                 #32
ld([Y,X])                       #33
st([Y,Xpp])                     #34 Just X++
st([sysArgs+7])                 #35

ld([vAC],X)                     #36 Screen memory destination address
ld([vAC+1],Y)                   #37
ld([sysArgs+2])                 #38 Write 6 pixels
st([Y,Xpp])                     #39
ld([sysArgs+3])                 #40
st([Y,Xpp])                     #41
ld([sysArgs+4])                 #42
st([Y,Xpp])                     #43
ld([sysArgs+5])                 #44
st([Y,Xpp])                     #45
ld([sysArgs+6])                 #46
st([Y,Xpp])                     #47
ld([sysArgs+7])                 #48
st([Y,Xpp])                     #49

ld([sysArgs+0])                 #50 src += 6
adda(6)                         #51
st([sysArgs+0])                 #52
ld([vAC+1])                     #53 dst += 256
adda(1)                         #54
st([vAC+1])                     #55

ld([vPC])                       #56 Self-repeating SYS call
suba(2)                         #57
st([vPC])                       #58
ld(hi('REENTER'),Y)             #59
jmp(Y,'REENTER')                #60
ld(-64/2)                       #61

align(64)
label('SYS_Sprite6x_v3_64')

ld([sysArgs+0],X)               #15 Pixel data source address
ld([sysArgs+1],Y)               #16
ld([Y,X])                       #17 Next pixel or stop
bpl('.sysDpx1')                 #18
st([Y,Xpp])                     #19 Just X++

adda([vAC+1])                   #20 Adjust dst for convenience
st([vAC+1])                     #21
ld([vAC])                       #22
suba(6)                         #23
st([vAC])                       #24
ld([sysArgs+0])                 #25 Adjust src for convenience
adda(1)                         #26
st([sysArgs+0])                 #27
nop()                           #28
ld(hi('REENTER'),Y)             #29 Normal exit (no self-repeat)
jmp(Y,'REENTER')                #30
ld(-34/2)                       #31

label('.sysDpx1')
st([sysArgs+7])                 #20 Gobble 6 pixels into buffer (backwards)
ld([Y,X])                       #21
st([Y,Xpp])                     #22 Just X++
st([sysArgs+6])                 #23
ld([Y,X])                       #24
st([Y,Xpp])                     #25 Just X++
st([sysArgs+5])                 #26
ld([Y,X])                       #27
st([Y,Xpp])                     #28 Just X++
st([sysArgs+4])                 #29
ld([Y,X])                       #30
st([Y,Xpp])                     #31 Just X++
st([sysArgs+3])                 #32
ld([Y,X])                       #33
st([Y,Xpp])                     #34 Just X++

ld([vAC],X)                     #35 Screen memory destination address
ld([vAC+1],Y)                   #36
st([Y,Xpp])                     #37 Write 6 pixels
ld([sysArgs+3])                 #38
st([Y,Xpp])                     #39
ld([sysArgs+4])                 #40
st([Y,Xpp])                     #41
ld([sysArgs+5])                 #42
st([Y,Xpp])                     #43
ld([sysArgs+6])                 #44
st([Y,Xpp])                     #45
ld([sysArgs+7])                 #46
st([Y,Xpp])                     #47

ld([sysArgs+0])                 #48 src += 6
adda(6)                         #49
st([sysArgs+0])                 #50
ld([vAC+1])                     #51 dst += 256
adda(1)                         #52
st([vAC+1])                     #53

ld([vPC])                       #54 Self-repeating SYS call
suba(2)                         #55
st([vPC])                       #56
ld(hi('REENTER'),Y)             #57
jmp(Y,'REENTER')                #58
ld(-62/2)                       #59

align(64)
label('SYS_Sprite6y_v3_64')

ld([sysArgs+0],X)               #15 Pixel data source address
ld([sysArgs+1],Y)               #16
ld([Y,X])                       #17 Next pixel or stop
bpl('.sysDpx2')                 #18
st([Y,Xpp])                     #19 Just X++

xora(255)                       #20 Adjust dst for convenience
adda(1)                         #21
adda([vAC+1])                   #22
st([vAC+1])                     #23
ld([vAC])                       #24
adda(6)                         #25
st([vAC])                       #26
ld([sysArgs+0])                 #27 Adjust src for convenience
adda(1)                         #28
st([sysArgs+0])                 #29
nop()                           #30
ld(hi('REENTER'),Y)             #31 Normal exit (no self-repeat)
jmp(Y,'REENTER')                #32
ld(-36/2)                       #33

label('.sysDpx2')
st([sysArgs+2])                 #20 Gobble 6 pixels into buffer
ld([Y,X])                       #21
st([Y,Xpp])                     #22 Just X++
st([sysArgs+3])                 #23
ld([Y,X])                       #24
st([Y,Xpp])                     #25 Just X++
st([sysArgs+4])                 #26
ld([Y,X])                       #27
st([Y,Xpp])                     #28 Just X++
st([sysArgs+5])                 #29
ld([Y,X])                       #30
st([Y,Xpp])                     #31 Just X++
st([sysArgs+6])                 #32
ld([Y,X])                       #33
st([Y,Xpp])                     #34 Just X++
st([sysArgs+7])                 #35

ld([vAC],X)                     #36 Screen memory destination address
ld([vAC+1],Y)                   #37
ld([sysArgs+2])                 #38 Write 6 pixels
st([Y,Xpp])                     #39
ld([sysArgs+3])                 #40
st([Y,Xpp])                     #41
ld([sysArgs+4])                 #42
st([Y,Xpp])                     #43
ld([sysArgs+5])                 #44
st([Y,Xpp])                     #45
ld([sysArgs+6])                 #46
st([Y,Xpp])                     #47
ld([sysArgs+7])                 #48
st([Y,Xpp])                     #49

ld([sysArgs+0])                 #50 src += 6
adda(6)                         #51
st([sysArgs+0])                 #52
ld([vAC+1])                     #53 dst -= 256
suba(1)                         #54
st([vAC+1])                     #55

ld([vPC])                       #56 Self-repeating SYS call
suba(2)                         #57
st([vPC])                       #58
ld(hi('REENTER'),Y)             #59
jmp(Y,'REENTER')                #60
ld(-64/2)                       #61

align(64)
label('SYS_Sprite6xy_v3_64')

ld([sysArgs+0],X)               #15 Pixel data source address
ld([sysArgs+1],Y)               #16
ld([Y,X])                       #17 Next pixel or stop
bpl('.sysDpx3')                 #18
st([Y,Xpp])                     #19 Just X++

xora(255)                       #20 Adjust dst for convenience
adda(1)                         #21
adda([vAC+1])                   #22
st([vAC+1])                     #23
ld([vAC])                       #24
suba(6)                         #25
st([vAC])                       #26
ld([sysArgs+0])                 #27 Adjust src for convenience
adda(1)                         #28
st([sysArgs+0])                 #29
nop()                           #30
ld(hi('REENTER'),Y)             #31 Normal exit (no self-repeat)
jmp(Y,'REENTER')                #32
ld(-36/2)                       #33

label('.sysDpx3')
st([sysArgs+7])                 #20 Gobble 6 pixels into buffer (backwards)
ld([Y,X])                       #21
st([Y,Xpp])                     #22 Just X++
st([sysArgs+6])                 #23
ld([Y,X])                       #24
st([Y,Xpp])                     #25 Just X++
st([sysArgs+5])                 #26
ld([Y,X])                       #27
st([Y,Xpp])                     #28 Just X++
st([sysArgs+4])                 #29
ld([Y,X])                       #30
st([Y,Xpp])                     #31 Just X++
st([sysArgs+3])                 #32
ld([Y,X])                       #33
st([Y,Xpp])                     #34 Just X++

ld([vAC],X)                     #35 Screen memory destination address
ld([vAC+1],Y)                   #36
st([Y,Xpp])                     #37 Write 6 pixels
ld([sysArgs+3])                 #38
st([Y,Xpp])                     #39
ld([sysArgs+4])                 #40
st([Y,Xpp])                     #41
ld([sysArgs+5])                 #42
st([Y,Xpp])                     #43
ld([sysArgs+6])                 #44
st([Y,Xpp])                     #45
ld([sysArgs+7])                 #46
st([Y,Xpp])                     #47

ld([sysArgs+0])                 #48 src += 6
adda(6)                         #49
st([sysArgs+0])                 #50
ld([vAC+1])                     #51 dst -= 256
suba(1)                         #52
st([vAC+1])                     #53

ld([vPC])                       #54 Self-repeating SYS call
suba(2)                         #55
st([vPC])                       #56
ld(hi('REENTER'),Y)             #57
jmp(Y,'REENTER')                #58
ld(-62/2)                       #59

#-----------------------------------------------------------------------

align(0x100, size=0x100)

label('sys_ExpanderControl')
ld(hi(ctrlBits),Y)                  #18
anda([vAC])                         #19 check for special ctrl code space
beq('sysEx#22')                     #20
ld([vAC])                           #21 load low byte of ctrl code in delay slot
anda(0xfc)                          #22 sanitize normal ctrl code
st([Y,ctrlBits])                    #23 store in ctrlBits
if WITH_512K_BOARD:
  ld(AC,X)                            #24
  ld([vAC+1],Y)                       #25
  ctrl(Y,X)                           #26 issue ctrl code
  label('sysEx#27')
  ld(hi('REENTER'),Y)                 #27
  jmp(Y,'REENTER')                    #28
  ld(-32/2)                           #29
  label('sysEx#22')
  anda(0xfc,X)                        #22 special ctrl code
  ld([vAC+1],Y)                       #23
  xora(0xf0)                          #24
  bne('sysEx#27')                     #25
  ctrl(Y,X)                           #26 issue ctrl code
  ld([vAC+1])                         #27
  xora([videoModeC])                  #28
  anda(0xfe)                          #29 Save 7 bits of extended banking
  xora([videoModeC])                  #30 code into videomodeC.
  st([videoModeC])                    #31
  ld(hi('NEXTY'),Y)                   #32
  jmp(Y,'NEXTY')                      #33
  ld(-36/2)                           #34
elif WITH_128K_BOARD:
  st([ctrlCopy],X)                    #24
  xora([ctrlVideo])                   #25
  anda(0x3c)                          #26
  xora([ctrlVideo])                   #27
  label('sysEx#28')
  st([ctrlVideo])                     #28
  ld([vAC+1],Y)                       #29
  ctrl(Y,X)                           #30 issue ctrl code
  ld([ctrlCopy])                      #31 always read after ctrl
  ld(hi('NEXTY'),Y)                   #32
  jmp(Y,'NEXTY')                      #33
  ld(-36/2)                           #34
  label('sysEx#22')
  anda(0xfc,X)                        #22 special ctrl code
  ld([vAC+1],Y)                       #23
  ctrl(Y,X)                           #24 issue special code
  ld([ctrlCopy],X)                    #25 from last time (hopefully)
  bra('sysEx#28')                     #26
  ld([ctrlVideo])                     #27
else:
  st([vTmp])                          #24 store in vTmp
  bra('sysEx#27')                     #25 jump to issuing normal ctrl code
  ld([vAC+1],Y)                       #26 load high byte of ctrl code in delay slot
  label('sysEx#22')
  anda(0xfc,X)                        #22 * special ctrl code
  ld([Y,ctrlBits])                    #23 get previous normal code from ctrlBits
  st([vTmp])                          #24 save it in vTmp
  ld([vAC+1],Y)                       #25 load high byte of ctrl code
  ctrl(Y,X)                           #26 issue special ctrl code
  label('sysEx#27')
  ld([vTmp])                          #27 load saved normal ctrl code
  anda(0xfc,X)                        #28 sanitize ctrlBits
  ctrl(Y,X)                           #29 issue normal ctrl code
  ld([vTmp])                          #30 always load something after ctrl
  ld(hi('REENTER'),Y)                 #31
  jmp(Y,'REENTER')                    #32
  ld(-36/2)                           #33


#-----------------------------------------------------------------------

label('sys_SpiExchangeBytes')

ld([Y,ctrlBits])                #18
st([sysArgs+4])                 #19

ld([sysArgs+0],X)               #20 Fetch byte to send
ld([sysArgs+1],Y)               #21
ld([Y,X])                       #22

for i in range(8):
  st([vTmp],Y);C('Bit %d'%(7-i))#23+i*12
  ld([sysArgs+4],X)             #24+i*12
  ctrl(Y,Xpp)                   #25+i*12 Set MOSI
  ctrl(Y,Xpp)                   #26+i*12 Raise SCLK, disable RAM!
  ld([0])                       #27+i*12 Get MISO
  if 1 <= WITH_SPI_BITS <= 4:
    anda((1<<WITH_SPI_BITS)-1)  #28+i*12
  else:
    anda(0b00001111)            #28+i*12 This is why R1 as pull-DOWN is simpler
  beq(pc()+3)                   #29+i*12
  bra(pc()+2)                   #30+i*12
  ld(1)                         #31+i*12
  ctrl(Y,X)                     #32+i*12,29+i*12 (Must be idempotent) Lower SCLK
  adda([vTmp])                  #33+i*12 Shift
  adda([vTmp])                  #34+i*12

ld([sysArgs+0],X)               #119 Store received byte
ld([sysArgs+3],Y)               #120
st([Y,X])                       #121

ld([sysArgs+0])                 #122 Advance pointer
adda(1)                         #123
st([sysArgs+0])                 #124

xora([sysArgs+2])               #125 Reached end?
beq('.sysSpi#128')              #126

ld([vPC])                       #127 Self-repeating SYS call
suba(2)                         #128
st([vPC])                       #129
ld(hi('NEXTY'),Y)               #130
jmp(Y,'NEXTY')                  #131
ld(-134/2)                      #132

label('.sysSpi#128')
ld(hi('NEXTY'),Y)               #128 Continue program
jmp(Y,'NEXTY')                  #129
ld(-132/2)                      #130

#-----------------------------------------------------------------------

label('sys_v6502')

st([vCpuSelect],Y)              #18 Activate v6502
ld(-22/2)                       #19
jmp(Y,'v6502_ENTER')            #20 Transfer control in the same time slice
adda([vTicks])                  #21
assert (38 - 22)//2 >= v6502_adjust

#-----------------------------------------------------------------------
#       MOS 6502 emulator
#-----------------------------------------------------------------------

# Some quirks:
# - Stack in zero page instead of page 1
# - No interrupts
# - No decimal mode (may never be added). D flag is emulated but ignored.
# - BRK switches back to running 16-bits vCPU
# - Illegal opcodes map to BRK, but can read ghost operands before trapping
# - Illegal opcode $ff won't be trapped and cause havoc instead

# Big things TODO:
# XXX Tuning, put most frequent instructions in the primary page

label('v6502_ror')
assert v6502_Cflag == 1
ld([v6502_ADH],Y)               #12
ld(-46//2+v6502_maxTicks)       #13 Is there enough time for the excess ticks?
adda([vTicks])                  #14
blt('.recheck17')               #15
ld([v6502_P])                   #16 Transfer C to "bit 8"
anda(1)                         #17
adda(127)                       #18
anda(128)                       #19
st([v6502_BI])                  #20 The real 6502 wouldn't use BI for this
ld([Y,X])                       #21 Transfer bit 0 to C
xora([v6502_P])                 #22
anda(1)                         #23
xora([v6502_P])                 #24
st([v6502_P])                   #25
ld('v6502_ror#36')              #26 Shift table lookup
st([vTmp])                      #27
ld([Y,X])                       #28
anda(~1)                        #29
ld(hi('shiftTable'),Y)          #30
jmp(Y,AC)                       #31
bra(255)                        #32 bra shiftTable+255
label('.recheck17')
ld(hi('v6502_check'),Y)         #17 Go back to time check before dispatch
jmp(Y,'v6502_check')            #18
ld(-20/2)                       #19

label('v6502_lsr')
assert v6502_Cflag == 1
ld([v6502_ADH],Y)               #12
ld([Y,X])                       #13 Transfer bit 0 to C
xora([v6502_P])                 #14
anda(1)                         #15
xora([v6502_P])                 #16
st([v6502_P])                   #17
ld('v6502_lsr#28')              #18 Shift table lookup
st([vTmp])                      #19
ld([Y,X])                       #20
anda(~1)                        #21
ld(hi('shiftTable'),Y)          #22
jmp(Y,AC)                       #23
bra(255)                        #24 bra shiftTable+255

label('v6502_rol')
assert v6502_Cflag == 1
ld([v6502_ADH],Y)               #12
ld([Y,X])                       #13
anda(0x80)                      #14
st([v6502_Tmp])                 #15
ld([v6502_P])                   #16
anda(1)                         #17
label('.rol#18')
adda([Y,X])                     #18
adda([Y,X])                     #19
st([Y,X])                       #20
st([v6502_Qz])                  #21 Z flag
st([v6502_Qn])                  #22 N flag
ld([v6502_P])                   #23 C Flag
anda(~1)                        #24
ld([v6502_Tmp],X)               #25
ora([X])                        #26
st([v6502_P])                   #27
ld(hi('v6502_next'),Y)          #28
ld(-32/2)                       #29
jmp(Y,'v6502_next')             #30
#nop()                          #31 Overlap
#
label('v6502_asl')
ld([v6502_ADH],Y)               #12,32
ld([Y,X])                       #13
anda(0x80)                      #14
st([v6502_Tmp])                 #15
bra('.rol#18')                  #16
ld(0)                           #17

label('v6502_jmp1')
nop()                           #12
ld([v6502_ADL])                 #13
st([v6502_PCL])                 #14
ld([v6502_ADH])                 #15
st([v6502_PCH])                 #16
ld(hi('v6502_next'),Y)          #17
jmp(Y,'v6502_next')             #18
ld(-20/2)                       #19

label('v6502_jmp2')
nop()                           #12
ld([v6502_ADH],Y)               #13
ld([Y,X])                       #14
st([Y,Xpp])                     #15 (Just X++) Wrap around: bug compatible with NMOS
st([v6502_PCL])                 #16
ld([Y,X])                       #17
st([v6502_PCH])                 #18
ld(hi('v6502_next'),Y)          #19
jmp(Y,'v6502_next')             #20
ld(-22/2)                       #21

label('v6502_pla')
ld([v6502_S])                   #12
ld(AC,X)                        #13
adda(1)                         #14
st([v6502_S])                   #15
ld([X])                         #16
st([v6502_A])                   #17
st([v6502_Qz])                  #18 Z flag
st([v6502_Qn])                  #19 N flag
ld(hi('v6502_next'),Y)          #20
ld(-24/2)                       #21
jmp(Y,'v6502_next')             #22
#nop()                          #23 Overlap
#
label('v6502_pha')
ld(hi('v6502_next'),Y)          #12,24
ld([v6502_S])                   #13
suba(1)                         #14
st([v6502_S],X)                 #15
ld([v6502_A])                   #16
st([X])                         #17
jmp(Y,'v6502_next')             #18
ld(-20/2)                       #19

label('v6502_brk')
ld(hi('ENTER'))                 #12 Switch to vCPU
st([vCpuSelect])                #13
assert v6502_A == vAC
ld(0)                           #14
st([vAC+1])                     #15
ld(hi('REENTER'),Y)             #16 Switch in the current time slice
ld(-22//2+v6502_adjust)         #17
jmp(Y,'REENTER')                #18
nop()                           #19

# All interpreter entry points must share the same page offset, because
# this offset is hard-coded as immediate operand in the video driver.
# The Gigatron's original vCPU's 'ENTER' label is already at $2ff, so we
# just use $dff for 'v6502_ENTER'. v6502 actually has two entry points.
# The other is 'v6502_RESUME' at $10ff. It is used for instructions
# that were fetched but not yet executed. Allowing the split gives finer
# granulariy, and hopefully more throughput for the simpler instructions.
# (There is no "overhead" for allowing instruction splitting, because
#  both emulation phases must administer [vTicks] anyway.)

fillers(until=0xff)
label('v6502_ENTER')
bra('v6502_next2')              #0 v6502 primary entry point
# --- Page boundary ---
align(0x100, size=0x100)
suba(v6502_adjust)              #1,19 Adjust for vCPU/v6520 timing differences

#19 Addressing modes
(   'v6502_mode0'  ); bra('v6502_modeIZX'); bra('v6502_modeIMM'); bra('v6502_modeILL') # $00 xxx000xx
bra('v6502_modeZP');  bra('v6502_modeZP');  bra('v6502_modeZP');  bra('v6502_modeILL') # $04 xxx001xx
bra('v6502_modeIMP'); bra('v6502_modeIMM'); bra('v6502_modeACC'); bra('v6502_modeILL') # $08 xxx010xx
bra('v6502_modeABS'); bra('v6502_modeABS'); bra('v6502_modeABS'); bra('v6502_modeILL') # $0c xxx011xx
bra('v6502_modeREL'); bra('v6502_modeIZY'); bra('v6502_modeIMM'); bra('v6502_modeILL') # $10 xxx100xx
bra('v6502_modeZPX'); bra('v6502_modeZPX'); bra('v6502_modeZPX'); bra('v6502_modeILL') # $14 xxx101xx
bra('v6502_modeIMP'); bra('v6502_modeABY'); bra('v6502_modeIMP'); bra('v6502_modeILL') # $18 xxx110xx
bra('v6502_modeABX'); bra('v6502_modeABX'); bra('v6502_modeABX'); bra('v6502_modeILL') # $1c xxx111xx

# Special encoding cases for emulator:
#     $00 BRK -         but gets mapped to #$DD      handled in v6502_mode0
#     $20 JSR $DDDD     but gets mapped to #$DD      handled in v6502_mode0 and v6502_JSR
#     $40 RTI -         but gets mapped to #$DD      handled in v6502_mode0
#     $60 RTS -         but gets mapped to #$DD      handled in v6502_mode0
#     $6C JMP ($DDDD)   but gets mapped to $DDDD     handled in v6502_JMP2
#     $96 STX $DD,Y     but gets mapped to $DD,X     handled in v6502_STX2
#     $B6 LDX $DD,Y     but gets mapped to $DD,X     handled in v6502_LDX2
#     $BE LDX $DDDD,Y   but gets mapped to $DDDD,X   handled in v6502_modeABX

label('v6502_next')
adda([vTicks])                  #0
blt('v6502_exitBefore')         #1 No more ticks
label('v6502_next2')
st([vTicks])                    #2
#
# Fetch opcode
ld([v6502_PCL],X)               #3
ld([v6502_PCH],Y)               #4
ld([Y,X])                       #5 Fetch IR
st([v6502_IR])                  #6
ld([v6502_PCL])                 #7 PC++
adda(1)                         #8
st([v6502_PCL],X)               #9
beq(pc()+3)                     #10
bra(pc()+3)                     #11
ld(0)                           #12
ld(1)                           #12(!)
adda([v6502_PCH])               #13
st([v6502_PCH],Y)               #14
#
# Get addressing mode and fetch operands
ld([v6502_IR])                  #15 Get addressing mode
anda(31)                        #16
bra(AC)                         #17
bra('.next20')                  #18
# (jump table)                  #19
label('.next20')
ld([Y,X])                       #20 Fetch L
# Most opcodes branch away at this point, but IR & 31 == 0 falls through
#
# Implicit Mode for  BRK JSR RTI RTS (<  0x80) -- 26 cycles
# Immediate Mode for LDY CPY CPX     (>= 0x80) -- 36 cycles
label('v6502_mode0')
ld([v6502_IR])                  #21 'xxx0000'
bmi('.imm24')                   #22
ld([v6502_PCH])                 #23
bra('v6502_check')              #24
ld(-26/2)                       #25

# Resync with video driver. At this point we're returning BEFORE
# fetching and executing the next instruction.
label('v6502_exitBefore')
adda(v6502_maxTicks)            #3 Exit BEFORE fetch
bgt(pc()&255)                   #4 Resync
suba(1)                         #5
ld(hi('v6502_ENTER'))           #6 Set entry point to before 'fetch'
st([vCpuSelect])                #7
ld(hi('vBlankStart'),Y)         #8
jmp(Y,[vReturn])                #9 To video driver
ld([channel])                   #10
assert v6502_overhead ==         11

# Immediate Mode: #$FF -- 36 cycles
label('v6502_modeIMM')
nop()                           #21 Wait for v6502_mode0 to join
nop()                           #22
ld([v6502_PCH])                 #23 Copy PC
label('.imm24')
st([v6502_ADH])                 #24
ld([v6502_PCL])                 #25
st([v6502_ADL],X)               #26
adda(1)                         #27 PC++
st([v6502_PCL])                 #28
beq(pc()+3)                     #29
bra(pc()+3)                     #30
ld(0)                           #31
ld(1)                           #31(!)
adda([v6502_PCH])               #32
st([v6502_PCH])                 #33
bra('v6502_check')              #34
ld(-36/2)                       #35

# Accumulator Mode: ROL ROR LSL ASR -- 28 cycles
label('v6502_modeACC')
ld(v6502_A&255)                 #21 Address of AC
st([v6502_ADL],X)               #22
ld(v6502_A>>8)                  #23
st([v6502_ADH])                 #24
ld(-28/2)                       #25
bra('v6502_check')              #26
#nop()                          #27 Overlap
#
# Implied Mode: no operand -- 24 cycles
label('v6502_modeILL')
label('v6502_modeIMP')
nop()                           #21,27
bra('v6502_check')              #22
ld(-24/2)                       #23

# Zero Page Modes: $DD $DD,X $DD,Y -- 36 cycles
label('v6502_modeZPX')
bra('.zp23')                    #21
adda([v6502_X])                 #22
label('v6502_modeZP')
bra('.zp23')                    #21
nop()                           #22
label('.zp23')
st([v6502_ADL],X)               #23
ld(0)                           #24 H=0
st([v6502_ADH])                 #25
ld(1)                           #26 PC++
adda([v6502_PCL])               #27
st([v6502_PCL])                 #28
beq(pc()+3)                     #29
bra(pc()+3)                     #30
ld(0)                           #31
ld(1)                           #31(!)
adda([v6502_PCH])               #32
st([v6502_PCH])                 #33
bra('v6502_check')              #34
ld(-36/2)                       #35

# Possible retry loop for modeABS and modeIZY. Because these need
# more time than the v6502_maxTicks of 38 Gigatron cycles, we may
# have to restart them after the next horizontal pulse.
label('.retry28')
beq(pc()+3)                     #28,37 PC--
bra(pc()+3)                     #29
ld(0)                           #30
ld(-1)                          #30(!)
adda([v6502_PCH])               #31
st([v6502_PCH])                 #32
ld([v6502_PCL])                 #33
suba(1)                         #34
st([v6502_PCL])                 #35
bra('v6502_next')               #36 Retry until sufficient time
ld(-38/2)                       #37

# Absolute Modes: $DDDD $DDDD,X $DDDD,Y -- 64 cycles
label('v6502_modeABS')
bra('.abs23')                   #21
ld(0)                           #22
label('v6502_modeABX')
bra('.abs23')                   #21
label('v6502_modeABY')
ld([v6502_X])                   #21,22
ld([v6502_Y])                   #22
label('.abs23')
st([v6502_ADL])                 #23
ld(-64//2+v6502_maxTicks)       #24 Is there enough time for the excess ticks?
adda([vTicks])                  #25
blt('.retry28')                 #26
ld([v6502_PCL])                 #27
ld([v6502_IR])                  #28 Special case $BE: LDX $DDDD,Y (we got X in ADL)
xora(0xbe)                      #29
beq(pc()+3)                     #30
bra(pc()+3)                     #31
ld([v6502_ADL])                 #32
ld([v6502_Y])                   #32(!)
adda([Y,X])                     #33 Fetch and add L
st([v6502_ADL])                 #34
bmi('.abs37')                   #35 Carry?
suba([Y,X])                     #36 Gets back original operand
bra('.abs39')                   #37
ora([Y,X])                      #38 Carry in bit 7
label('.abs37')
anda([Y,X])                     #37 Carry in bit 7
nop()                           #38
label('.abs39')
anda(0x80,X)                    #39 Move carry to bit 0
ld([X])                         #40
st([v6502_ADH])                 #41
ld([v6502_PCL])                 #42 PC++
adda(1)                         #43
st([v6502_PCL],X)               #44
beq(pc()+3)                     #45
bra(pc()+3)                     #46
ld(0)                           #47
ld(1)                           #47(!)
adda([v6502_PCH])               #48
st([v6502_PCH],Y)               #49
ld([Y,X])                       #50 Fetch H
adda([v6502_ADH])               #51
st([v6502_ADH])                 #52
ld([v6502_PCL])                 #53 PC++
adda(1)                         #54
st([v6502_PCL])                 #55
beq(pc()+3)                     #56
bra(pc()+3)                     #57
ld(0)                           #58
ld(1)                           #58(!)
adda([v6502_PCH])               #59
st([v6502_PCH])                 #60
ld([v6502_ADL],X)               #61
bra('v6502_check')              #62
ld(-64/2)                       #63

# Indirect Indexed Mode: ($DD),Y -- 54 cycles
label('v6502_modeIZY')
ld(AC,X)                        #21 $DD
ld(0,Y)                         #22 $00DD
ld(-54//2+v6502_maxTicks)       #23 Is there enough time for the excess ticks?
adda([vTicks])                  #24
nop()                           #25
blt('.retry28')                 #26
ld([v6502_PCL])                 #27
adda(1)                         #28 PC++
st([v6502_PCL])                 #29
beq(pc()+3)                     #30
bra(pc()+3)                     #31
ld(0)                           #32
ld(1)                           #32(!)
adda([v6502_PCH])               #33
st([v6502_PCH])                 #34
ld([Y,X])                       #35 Read word from zero-page
st([Y,Xpp])                     #36 (Just X++) Wrap-around is correct
st([v6502_ADL])                 #37
ld([Y,X])                       #38
st([v6502_ADH])                 #39
ld([v6502_Y])                   #40 Add Y
adda([v6502_ADL])               #41
st([v6502_ADL])                 #42
bmi('.izy45')                   #43 Carry?
suba([v6502_Y])                 #44 Gets back original operand
bra('.izy47')                   #45
ora([v6502_Y])                  #46 Carry in bit 7
label('.izy45')
anda([v6502_Y])                 #45 Carry in bit 7
nop()                           #46
label('.izy47')
anda(0x80,X)                    #47 Move carry to bit 0
ld([X])                         #48
adda([v6502_ADH])               #49
st([v6502_ADH])                 #50
ld([v6502_ADL],X)               #51
bra('v6502_check')              #52
ld(-54/2)                       #53

# Relative Mode: BEQ BNE BPL BMI BCC BCS BVC BVS -- 36 cycles
label('v6502_modeREL')
st([v6502_ADL],X)               #21 Offset (Only needed for branch)
bmi(pc()+3)                     #22 Sign extend
bra(pc()+3)                     #23
ld(0)                           #24
ld(255)                         #24(!)
st([v6502_ADH])                 #25
ld([v6502_PCL])                 #26 PC++ (Needed for both cases)
adda(1)                         #27
st([v6502_PCL])                 #28
beq(pc()+3)                     #29
bra(pc()+3)                     #30
ld(0)                           #31
ld(1)                           #31(!)
adda([v6502_PCH])               #32
st([v6502_PCH])                 #33
bra('v6502_check')              #34
ld(-36/2)                       #53

# Indexed Indirect Mode: ($DD,X) -- 38 cycles
label('v6502_modeIZX')
adda([v6502_X])                 #21 Add X
st([v6502_Tmp])                 #22
adda(1,X)                       #23 Read word from zero-page
ld([X])                         #24
st([v6502_ADH])                 #25
ld([v6502_Tmp],X)               #26
ld([X])                         #27
st([v6502_ADL],X)               #28
ld([v6502_PCL])                 #29 PC++
adda(1)                         #30
st([v6502_PCL])                 #31
beq(pc()+3)                     #32
bra(pc()+3)                     #33
ld(0)                           #34
ld(1)                           #34(!)
adda([v6502_PCH])               #35
st([v6502_PCH])                 #36
ld(-38/2)                       #37 !!! Fall through to v6502_check !!!
#
# Update elapsed time for the addressing mode processing.
# Then check if we can immediately execute this instruction.
# Otherwise transfer control to the video driver.
label('v6502_check')
adda([vTicks])                  #0
blt('v6502_exitAfter')          #1 No more ticks
st([vTicks])                    #2
ld(hi('v6502_execute'),Y)       #3
jmp(Y,[v6502_IR])               #4
bra(255)                        #5

# Otherwise resync with video driver. At this point we're returning AFTER
# addressing mode decoding, but before executing the instruction.
label('v6502_exitAfter')
adda(v6502_maxTicks)            #3 Exit AFTER fetch
bgt(pc()&255)                   #4 Resync
suba(1)                         #5
ld(hi('v6502_RESUME'))          #6 Set entry point to before 'execute'
st([vCpuSelect])                #7
ld(hi('vBlankStart'),Y)         #8
jmp(Y,[vReturn])                #9 To video driver
ld([channel])                   #10
assert v6502_overhead ==         11

align(0x100,size=0x100)
label('v6502_execute')
# This page works as a 255-entry (0..254) jump table for 6502 opcodes.
# Jumping into this page must have 'bra 255' in the branch delay slot
# in order to get out again and dispatch to the right continuation.
# X must hold [v6502_ADL],
# Y will hold hi('v6502_execute'),
# A will be loaded with the code offset (this is skipped at offset $ff)
ld('v6502_BRK'); ld('v6502_ORA'); ld('v6502_ILL'); ld('v6502_ILL') #6 $00
ld('v6502_ILL'); ld('v6502_ORA'); ld('v6502_ASL'); ld('v6502_ILL') #6
ld('v6502_PHP'); ld('v6502_ORA'); ld('v6502_ASL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_ORA'); ld('v6502_ASL'); ld('v6502_ILL') #6
ld('v6502_BPL'); ld('v6502_ORA'); ld('v6502_ILL'); ld('v6502_ILL') #6 $10
ld('v6502_ILL'); ld('v6502_ORA'); ld('v6502_ASL'); ld('v6502_ILL') #6
ld('v6502_CLC'); ld('v6502_ORA'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_ORA'); ld('v6502_ASL'); ld('v6502_ILL') #6
ld('v6502_JSR'); ld('v6502_AND'); ld('v6502_ILL'); ld('v6502_ILL') #6 $20
ld('v6502_BIT'); ld('v6502_AND'); ld('v6502_ROL'); ld('v6502_ILL') #6
ld('v6502_PLP'); ld('v6502_AND'); ld('v6502_ROL'); ld('v6502_ILL') #6
ld('v6502_BIT'); ld('v6502_AND'); ld('v6502_ROL'); ld('v6502_ILL') #6
ld('v6502_BMI'); ld('v6502_AND'); ld('v6502_ILL'); ld('v6502_ILL') #6 $30
ld('v6502_ILL'); ld('v6502_AND'); ld('v6502_ROL'); ld('v6502_ILL') #6
ld('v6502_SEC'); ld('v6502_AND'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_AND'); ld('v6502_ROL'); ld('v6502_ILL') #6
ld('v6502_RTI'); ld('v6502_EOR'); ld('v6502_ILL'); ld('v6502_ILL') #6 $40
ld('v6502_ILL'); ld('v6502_EOR'); ld('v6502_LSR'); ld('v6502_ILL') #6
ld('v6502_PHA'); ld('v6502_EOR'); ld('v6502_LSR'); ld('v6502_ILL') #6
ld('v6502_JMP1');ld('v6502_EOR'); ld('v6502_LSR'); ld('v6502_ILL') #6
ld('v6502_BVC'); ld('v6502_EOR'); ld('v6502_ILL'); ld('v6502_ILL') #6 $50
ld('v6502_ILL'); ld('v6502_EOR'); ld('v6502_LSR'); ld('v6502_ILL') #6
ld('v6502_CLI'); ld('v6502_EOR'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_EOR'); ld('v6502_LSR'); ld('v6502_ILL') #6
ld('v6502_RTS'); ld('v6502_ADC'); ld('v6502_ILL'); ld('v6502_ILL') #6 $60
ld('v6502_ILL'); ld('v6502_ADC'); ld('v6502_ROR'); ld('v6502_ILL') #6
ld('v6502_PLA'); ld('v6502_ADC'); ld('v6502_ROR'); ld('v6502_ILL') #6
ld('v6502_JMP2');ld('v6502_ADC'); ld('v6502_ROR'); ld('v6502_ILL') #6
ld('v6502_BVS'); ld('v6502_ADC'); ld('v6502_ILL'); ld('v6502_ILL') #6 $70
ld('v6502_ILL'); ld('v6502_ADC'); ld('v6502_ROR'); ld('v6502_ILL') #6
ld('v6502_SEI'); ld('v6502_ADC'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_ADC'); ld('v6502_ROR'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_STA'); ld('v6502_ILL'); ld('v6502_ILL') #6 $80
ld('v6502_STY'); ld('v6502_STA'); ld('v6502_STX'); ld('v6502_ILL') #6
ld('v6502_DEY'); ld('v6502_ILL'); ld('v6502_TXA'); ld('v6502_ILL') #6
ld('v6502_STY'); ld('v6502_STA'); ld('v6502_STX'); ld('v6502_ILL') #6
ld('v6502_BCC'); ld('v6502_STA'); ld('v6502_ILL'); ld('v6502_ILL') #6 $90
ld('v6502_STY'); ld('v6502_STA'); ld('v6502_STX2');ld('v6502_ILL') #6
ld('v6502_TYA'); ld('v6502_STA'); ld('v6502_TXS'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_STA'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_LDY'); ld('v6502_LDA'); ld('v6502_LDX'); ld('v6502_ILL') #6 $A0
ld('v6502_LDY'); ld('v6502_LDA'); ld('v6502_LDX'); ld('v6502_ILL') #6
ld('v6502_TAY'); ld('v6502_LDA'); ld('v6502_TAX'); ld('v6502_ILL') #6
ld('v6502_LDY'); ld('v6502_LDA'); ld('v6502_LDX'); ld('v6502_ILL') #6
ld('v6502_BCS'); ld('v6502_LDA'); ld('v6502_ILL'); ld('v6502_ILL') #6 $B0
ld('v6502_LDY'); ld('v6502_LDA'); ld('v6502_LDX2');ld('v6502_ILL') #6
ld('v6502_CLV'); ld('v6502_LDA'); ld('v6502_TSX'); ld('v6502_ILL') #6
ld('v6502_LDY'); ld('v6502_LDA'); ld('v6502_LDX'); ld('v6502_ILL') #6
ld('v6502_CPY'); ld('v6502_CMP'); ld('v6502_ILL'); ld('v6502_ILL') #6 $C0
ld('v6502_CPY'); ld('v6502_CMP'); ld('v6502_DEC'); ld('v6502_ILL') #6
ld('v6502_INY'); ld('v6502_CMP'); ld('v6502_DEX'); ld('v6502_ILL') #6
ld('v6502_CPY'); ld('v6502_CMP'); ld('v6502_DEC'); ld('v6502_ILL') #6
ld('v6502_BNE'); ld('v6502_CMP'); ld('v6502_ILL'); ld('v6502_ILL') #6 $D0
ld('v6502_ILL'); ld('v6502_CMP'); ld('v6502_DEC'); ld('v6502_ILL') #6
ld('v6502_CLD'); ld('v6502_CMP'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_CMP'); ld('v6502_DEC'); ld('v6502_ILL') #6
ld('v6502_CPX'); ld('v6502_SBC'); ld('v6502_ILL'); ld('v6502_ILL') #6 $E0
ld('v6502_CPX'); ld('v6502_SBC'); ld('v6502_INC'); ld('v6502_ILL') #6
ld('v6502_INX'); ld('v6502_SBC'); ld('v6502_NOP'); ld('v6502_ILL') #6
ld('v6502_CPX'); ld('v6502_SBC'); ld('v6502_INC'); ld('v6502_ILL') #6
ld('v6502_BEQ'); ld('v6502_SBC'); ld('v6502_ILL'); ld('v6502_ILL') #6 $F0
ld('v6502_ILL'); ld('v6502_SBC'); ld('v6502_INC'); ld('v6502_ILL') #6
ld('v6502_SED'); ld('v6502_SBC'); ld('v6502_ILL'); ld('v6502_ILL') #6
ld('v6502_ILL'); ld('v6502_SBC'); ld('v6502_INC')                  #6
bra(AC)                         #6,7 Dispatch into next page
# --- Page boundary ---
align(0x100,size=0x100)
ld(hi('v6502_next'),Y)          #8 Handy for instructions that don't clobber Y

label('v6502_ADC')
assert pc()&255 == 1
assert v6502_Cflag == 1
assert v6502_Vemu == 128
ld([v6502_ADH],Y)               #9 Must be at page offset 1, so A=1
anda([v6502_P])                 #10 Carry in (AC=1 because lo('v6502_ADC')=1)
adda([v6502_A])                 #11 Sum
beq('.adc14')                   #12 Danger zone for dropping a carry
adda([Y,X])                     #13
st([v6502_Qz])                  #14 Z flag, don't overwrite left-hand side (A) yet
st([v6502_Qn])                  #15 N flag
xora([v6502_A])                 #16 V flag, (Q^A) & (B^Q) & 0x80
st([v6502_A])                   #17
ld([Y,X])                       #18
xora([v6502_Qz])                #19
anda([v6502_A])                 #20
anda(0x80)                      #21
st([v6502_Tmp])                 #22
ld([v6502_Qz])                  #23 Update A
st([v6502_A])                   #24
bmi('.adc27')                   #25 C flag
suba([Y,X])                     #26
bra('.adc29')                   #27
ora([Y,X])                      #28
label('.adc27')
anda([Y,X])                     #27
nop()                           #28
label('.adc29')
anda(0x80,X)                    #29
ld([v6502_P])                   #30 Update P
anda(~v6502_Vemu&~v6502_Cflag)  #31
ora([X])                        #32
ora([v6502_Tmp])                #33
st([v6502_P])                   #34
ld(hi('v6502_next'),Y)          #35
jmp(Y,'v6502_next')             #36
ld(-38/2)                       #37
# Cin=1, A=$FF, B=$DD --> Result=$DD, Cout=1, V=0
# Cin=0, A=$00, B=$DD --> Result=$DD, Cout=0, V=0
label('.adc14')
st([v6502_A])                   #14 Special case
st([v6502_Qz])                  #15 Z flag
st([v6502_Qn])                  #16 N flag
ld([v6502_P])                   #17
anda(0x7f)                      #18 V=0, keep C
st([v6502_P])                   #19
ld(hi('v6502_next'),Y)          #20
ld(-24/2)                       #21
jmp(Y,'v6502_next')             #22
#nop()                          #23 Overlap
#
label('v6502_SBC')
# No matter how hard we try, v6502_SBC always comes out a lot clumsier
# than v6502_ADC. And that one already barely fits in 38 cycles and is
# hard to follow. So we use a hack: transmorph our SBC into an ADC with
# inverted operand, and then dispatch again. Simple and effective.
ld([v6502_ADH],Y)               #9,24
ld([Y,X])                       #10
xora(255)                       #11 Invert right-hand side operand
st([v6502_BI])                  #12 Park modified operand for v6502_ADC
ld(v6502_BI&255)                #13 Address of BI
st([v6502_ADL],X)               #14
ld(v6502_BI>>8)                 #15
st([v6502_ADH])                 #16
ld(0x69)                        #17 ADC #$xx (Any ADC opcode will do)
st([v6502_IR])                  #18
ld(hi('v6502_check'),Y)         #20 Go back to time check before dispatch
jmp(Y,'v6502_check')            #20
ld(-22/2)                       #21

# Carry calculation table
#   L7 R7 C7   RX UC SC
#   -- -- -- | -- -- --
#    0  0  0 |  0  0  0
#    0  0  1 |  0  0  0
#    1  0  0 |  0  1 +1
#    1  0  1 |  0  0  0
#    0  1  0 | -1  1  0
#    0  1  1 | -1  0 -1
#    1  1  0 | -1  1  0
#    1  1  1 | -1  1  0
#   -- -- -- | -- -- --
#    ^  ^  ^    ^  ^  ^
#    |  |  |    |  |  `--- Carry of unsigned L + signed R: SC = RX + UC
#    |  |  |    |  `----- Carry of unsigned L + unsigned R: UC = C7 ? L7&R7 : L7|R7
#    |  |  |    `------- Sign extension of signed R
#    |  |  `--------- MSB of unextended L + R
#    |  `----------- MSB of right operand R
#    `------------- MSB of left operand L

label('v6502_CLC')
ld([v6502_P])                   #9
bra('.sec12')                   #10
label('v6502_SEC')
anda(~v6502_Cflag)              #9,11 Overlap
ld([v6502_P])                   #10
ora(v6502_Cflag)                #11
label('.sec12')
st([v6502_P])                   #12
nop()                           #13
label('.next14')
jmp(Y,'v6502_next')             #14
ld(-16/2)                       #15

label('v6502_BPL')
ld([v6502_Qn])                  #9
bmi('.next12')                  #10
bpl('.branch13')                #11
#nop()                          #12 Overlap
label('v6502_BMI')
ld([v6502_Qn])                  #9,12
bpl('.next12')                  #10
bmi('.branch13')                #11
#nop()                          #12 Overlap
label('v6502_BVC')
ld([v6502_P])                   #9,12
anda(v6502_Vemu)                #10
beq('.branch13')                #11
bne('.next14')                  #12
#nop()                          #13 Overlap
label('v6502_BVS')
ld([v6502_P])                   #9,13
anda(v6502_Vemu)                #10
bne('.branch13')                #11
beq('.next14')                  #12
#nop()                          #13 Overlap
label('v6502_BCC')
ld([v6502_P])                   #9,13
anda(v6502_Cflag)               #10
beq('.branch13')                #11
bne('.next14')                  #12
#nop()                          #13 Overlap
label('v6502_BCS')
ld([v6502_P])                   #9,13
anda(v6502_Cflag)               #10
bne('.branch13')                #11
beq('.next14')                  #12
#nop()                          #13 Overlap
label('v6502_BNE')
ld([v6502_Qz])                  #9,13
beq('.next12')                  #10
bne('.branch13')                #11
#nop()                          #12 Overlap
label('v6502_BEQ')
ld([v6502_Qz])                  #9,12
bne('.next12')                  #10
beq('.branch13')                #11
#nop()                          #12 Overlap
label('.branch13')
ld([v6502_ADL])                 #13,12 PC + offset
adda([v6502_PCL])               #14
st([v6502_PCL])                 #15
bmi('.bra0')                    #16 Carry
suba([v6502_ADL])               #17
bra('.bra1')                    #18
ora([v6502_ADL])                #19
label('.bra0')
anda([v6502_ADL])               #18
nop()                           #19
label('.bra1')
anda(0x80,X)                    #20
ld([X])                         #21
adda([v6502_ADH])               #22
adda([v6502_PCH])               #23
st([v6502_PCH])                 #24
nop()                           #25
jmp(Y,'v6502_next')             #26
ld(-28/2)                       #27

label('v6502_INX')
nop()                           #9
ld([v6502_X])                   #10
adda(1)                         #11
st([v6502_X])                   #12
label('.inx13')
st([v6502_Qz])                  #13 Z flag
st([v6502_Qn])                  #14 N flag
ld(-18/2)                       #15
jmp(Y,'v6502_next')             #16
nop()                           #17

label('.next12')
jmp(Y,'v6502_next')             #12
ld(-14/2)                       #13

label('v6502_DEX')
ld([v6502_X])                   #9
suba(1)                         #10
bra('.inx13')                   #11
st([v6502_X])                   #12

label('v6502_INY')
ld([v6502_Y])                   #9
adda(1)                         #10
bra('.inx13')                   #11
st([v6502_Y])                   #12

label('v6502_DEY')
ld([v6502_Y])                   #9
suba(1)                         #10
bra('.inx13')                   #11
st([v6502_Y])                   #12

label('v6502_NOP')
ld(-12/2)                       #9
jmp(Y,'v6502_next')             #10
#nop()                          #11 Overlap
#
label('v6502_AND')
ld([v6502_ADH],Y)               #9,11
ld([v6502_A])                   #10
bra('.eor13')                   #11
anda([Y,X])                     #12

label('v6502_ORA')
ld([v6502_ADH],Y)               #9
ld([v6502_A])                   #10
bra('.eor13')                   #11
label('v6502_EOR')
ora([Y,X])                      #12,9
#
#label('v6502_EOR')
#nop()                          #9 Overlap
ld([v6502_ADH],Y)               #10
ld([v6502_A])                   #11
xora([Y,X])                     #12
label('.eor13')
st([v6502_A])                   #13
st([v6502_Qz])                  #14 Z flag
st([v6502_Qn])                  #15 N flag
ld(hi('v6502_next'),Y)          #16
ld(-20/2)                       #17
jmp(Y,'v6502_next')             #18
#nop()                          #19 Overlap
#
label('v6502_JMP1')
ld(hi('v6502_jmp1'),Y)          #9,19 JMP $DDDD
jmp(Y,'v6502_jmp1')             #10
#nop()                          #11 Overlap
label('v6502_JMP2')
ld(hi('v6502_jmp2'),Y)          #9 JMP ($DDDD)
jmp(Y,'v6502_jmp2')             #10
#nop()                          #11 Overlap
label('v6502_JSR')
ld([v6502_S])                   #9,11
suba(2)                         #10
st([v6502_S],X)                 #11
ld(v6502_Stack>>8,Y)            #12
ld([v6502_PCH])                 #13 Let ADL,ADH point to L operand
st([v6502_ADH])                 #14
ld([v6502_PCL])                 #15
st([v6502_ADL])                 #16
adda(1)                         #17 Push ++PC
st([v6502_PCL])                 #18 Let PCL,PCH point to H operand
st([Y,Xpp])                     #19
beq(pc()+3)                     #20
bra(pc()+3)                     #21
ld(0)                           #22
ld(1)                           #22(!)
adda([v6502_PCH])               #23
st([v6502_PCH])                 #24
st([Y,X])                       #25
ld([v6502_ADL],X)               #26 Fetch L
ld([v6502_ADH],Y)               #27
ld([Y,X])                       #28
ld([v6502_PCL],X)               #29 Fetch H
st([v6502_PCL])                 #30
ld([v6502_PCH],Y)               #31
ld([Y,X])                       #32
st([v6502_PCH])                 #33
ld(hi('v6502_next'),Y)          #34
ld(-38/2)                       #35
jmp(Y,'v6502_next')             #36
#nop()                          #37 Overlap
#
label('v6502_INC')
ld(hi('v6502_inc'),Y)           #9,37
jmp(Y,'v6502_inc')              #10
#nop()                          #11 Overlap
label('v6502_LDA')
ld(hi('v6502_lda'),Y)           #9,11
jmp(Y,'v6502_lda')              #10
#nop()                          #11 Overlap
label('v6502_LDX')
ld(hi('v6502_ldx'),Y)           #9,11
jmp(Y,'v6502_ldx')              #10
#nop()                          #11 Overlap
label('v6502_LDX2')
ld(hi('v6502_ldx2'),Y)          #9,11
jmp(Y,'v6502_ldx2')             #10
#nop()                          #11 Overlap
label('v6502_LDY')
ld(hi('v6502_ldy'),Y)           #9,11
jmp(Y,'v6502_ldy')              #10
#nop()                          #11 Overlap
label('v6502_STA')
ld(hi('v6502_sta'),Y)           #9,11
jmp(Y,'v6502_sta')              #10
#nop()                          #11 Overlap
label('v6502_STX')
ld(hi('v6502_stx'),Y)           #9,11
jmp(Y,'v6502_stx')              #10
#nop()                          #11 Overlap
label('v6502_STX2')
ld(hi('v6502_stx2'),Y)          #9,11
jmp(Y,'v6502_stx2')             #10
#nop()                          #11 Overlap
label('v6502_STY')
ld(hi('v6502_sty'),Y)           #9,11
jmp(Y,'v6502_sty')              #10
#nop()                          #11 Overlap
label('v6502_TAX')
ld(hi('v6502_tax'),Y)           #9,11
jmp(Y,'v6502_tax')              #10
#nop()                          #11 Overlap
label('v6502_TAY')
ld(hi('v6502_tay'),Y)           #9,11
jmp(Y,'v6502_tay')              #10
#nop()                          #11 Overlap
label('v6502_TXA')
ld(hi('v6502_txa'),Y)           #9,11
jmp(Y,'v6502_txa')              #10
#nop()                          #11 Overlap
label('v6502_TYA')
ld(hi('v6502_tya'),Y)           #9,11
jmp(Y,'v6502_tya')              #10
#nop()                          #11 Overlap
label('v6502_CLV')
ld(hi('v6502_clv'),Y)           #9,11
jmp(Y,'v6502_clv')              #10
#nop()                          #11 Overlap
label('v6502_RTI')
ld(hi('v6502_rti'),Y)           #9,11
jmp(Y,'v6502_rti')              #10
#nop()                          #11 Overlap
label('v6502_ROR')
ld(hi('v6502_ror'),Y)           #9,11
jmp(Y,'v6502_ror')              #10
#nop()                          #11 Overlap
label('v6502_LSR')
ld(hi('v6502_lsr'),Y)           #9,11
jmp(Y,'v6502_lsr')              #10
#nop()                          #11 Overlap
label('v6502_PHA')
ld(hi('v6502_pha'),Y)           #9,11
jmp(Y,'v6502_pha')              #10
#nop()                          #11 Overlap
label('v6502_CLI')
ld(hi('v6502_cli'),Y)           #9,11
jmp(Y,'v6502_cli')              #10
#nop()                          #11 Overlap
label('v6502_RTS')
ld(hi('v6502_rts'),Y)           #9,11
jmp(Y,'v6502_rts')              #10
#nop()                          #11 Overlap
label('v6502_PLA')
ld(hi('v6502_pla'),Y)           #9,11
jmp(Y,'v6502_pla')              #10
#nop()                          #11 Overlap
label('v6502_SEI')
ld(hi('v6502_sei'),Y)           #9,11
jmp(Y,'v6502_sei')              #10
#nop()                          #11 Overlap
label('v6502_TXS')
ld(hi('v6502_txs'),Y)           #9,11
jmp(Y,'v6502_txs')              #10
#nop()                          #11 Overlap
label('v6502_TSX')
ld(hi('v6502_tsx'),Y)           #9,11
jmp(Y,'v6502_tsx')              #10
#nop()                          #11 Overlap
label('v6502_CPY')
ld(hi('v6502_cpy'),Y)           #9,11
jmp(Y,'v6502_cpy')              #10
#nop()                          #11 Overlap
label('v6502_CMP')
ld(hi('v6502_cmp'),Y)           #9,11
jmp(Y,'v6502_cmp')              #10
#nop()                          #11 Overlap
label('v6502_DEC')
ld(hi('v6502_dec'),Y)           #9,11
jmp(Y,'v6502_dec')              #10
#nop()                          #11 Overlap
label('v6502_CLD')
ld(hi('v6502_cld'),Y)           #9,11
jmp(Y,'v6502_cld')              #10
#nop()                          #11 Overlap
label('v6502_CPX')
ld(hi('v6502_cpx'),Y)           #9,11
jmp(Y,'v6502_cpx')              #10
#nop()                          #11 Overlap
label('v6502_ASL')
ld(hi('v6502_asl'),Y)           #9,11
jmp(Y,'v6502_asl')              #10
#nop()                          #11 Overlap
label('v6502_PHP')
ld(hi('v6502_php'),Y)           #9,11
jmp(Y,'v6502_php')              #10
#nop()                          #11 Overlap
label('v6502_BIT')
ld(hi('v6502_bit'),Y)           #9
jmp(Y,'v6502_bit')              #10
#nop()                          #11 Overlap
label('v6502_ROL')
ld(hi('v6502_rol'),Y)           #9
jmp(Y,'v6502_rol')              #10
#nop()                          #11 Overlap
label('v6502_PLP')
ld(hi('v6502_plp'),Y)           #9
jmp(Y,'v6502_plp')              #10
#nop()                          #11 Overlap
label('v6502_SED')              # Decimal mode not implemented
ld(hi('v6502_sed'),Y)           #9,11
jmp(Y,'v6502_sed')              #10
#nop()                          #11 Overlap
label('v6502_ILL') # All illegal opcodes map to BRK, except $FF which will crash
label('v6502_BRK')
ld(hi('v6502_brk'),Y)           #9
jmp(Y,'v6502_brk')              #10
#nop()                          #11 Overlap

# `v6502_RESUME' is the interpreter's secondary entry point for when
# the opcode and operands were already fetched, just before the last hPulse.
# It must be at $xxff, prefably somewhere in v6502's own code pages.

fillers(until=0xff)
label('v6502_RESUME')
assert (pc()&255) == 255
suba(v6502_adjust)              #0,11 v6502 secondary entry point
# --- Page boundary ---
align(0x100,size=0x100)
st([vTicks])                    #1
ld([v6502_ADL],X)               #2
ld(hi('v6502_execute'),Y)       #3
jmp(Y,[v6502_IR])               #4
bra(255)                        #5

label('v6502_dec')
ld([v6502_ADH],Y)               #12
ld([Y,X])                       #13
suba(1)                         #14
st([Y,X])                       #15
st([v6502_Qz])                  #16 Z flag
st([v6502_Qn])                  #17 N flag
ld(hi('v6502_next'),Y)          #18
ld(-22/2)                       #19
jmp(Y,'v6502_next')             #20
#nop()                          #21 Overlap
#
label('v6502_inc')
ld([v6502_ADH],Y)               #12,22
ld([Y,X])                       #13
adda(1)                         #14
st([Y,X])                       #15
st([v6502_Qz])                  #16 Z flag
st([v6502_Qn])                  #17 N flag
ld(hi('v6502_next'),Y)          #18
ld(-22/2)                       #19
jmp(Y,'v6502_next')             #20
nop()                           #21

label('v6502_lda')
nop()                           #12
ld([v6502_ADH],Y)               #13
ld([Y,X])                       #14
st([v6502_A])                   #15
label('.lda16')
st([v6502_Qz])                  #16 Z flag
st([v6502_Qn])                  #17 N flag
nop()                           #18
ld(hi('v6502_next'),Y)          #19
jmp(Y,'v6502_next')             #20
ld(-22/2)                       #21

label('v6502_ldx')
ld([v6502_ADH],Y)               #12
ld([Y,X])                       #13
bra('.lda16')                   #14
st([v6502_X])                   #15

label('v6502_ldy')
ld([v6502_ADH],Y)               #12
ld([Y,X])                       #13
bra('.lda16')                   #14
st([v6502_Y])                   #15

label('v6502_ldx2')
ld([v6502_ADL])                 #12 Special case $B6: LDX $DD,Y
suba([v6502_X])                 #13 Undo X offset
adda([v6502_Y],X)               #14 Apply Y instead
ld([X])                         #15
st([v6502_X])                   #16
st([v6502_Qz])                  #17 Z flag
st([v6502_Qn])                  #18 N flag
ld(hi('v6502_next'),Y)          #19
jmp(Y,'v6502_next')             #20
ld(-22/2)                       #21

label('v6502_sta')
ld([v6502_ADH],Y)               #12
ld([v6502_A])                   #13
st([Y,X])                       #14
ld(hi('v6502_next'),Y)          #15
jmp(Y,'v6502_next')             #16
ld(-18/2)                       #17

label('v6502_stx')
ld([v6502_ADH],Y)               #12
ld([v6502_X])                   #13
st([Y,X])                       #14
ld(hi('v6502_next'),Y)          #15
jmp(Y,'v6502_next')             #16
ld(-18/2)                       #17

label('v6502_stx2')
ld([v6502_ADL])                 #12 Special case $96: STX $DD,Y
suba([v6502_X])                 #13 Undo X offset
adda([v6502_Y],X)               #14 Apply Y instead
ld([v6502_X])                   #15
st([X])                         #16
ld(hi('v6502_next'),Y)          #17
jmp(Y,'v6502_next')             #18
ld(-20/2)                       #19

label('v6502_sty')
ld([v6502_ADH],Y)               #12
ld([v6502_Y])                   #13
st([Y,X])                       #14
ld(hi('v6502_next'),Y)          #15
jmp(Y,'v6502_next')             #16
label('v6502_tax')
ld(-18/2)                       #17,12
#
#label('v6502_tax')
#nop()                          #12 Overlap
ld([v6502_A])                   #13
st([v6502_X])                   #14
label('.tax15')
st([v6502_Qz])                  #15 Z flag
st([v6502_Qn])                  #16 N flag
ld(hi('v6502_next'),Y)          #17
jmp(Y,'v6502_next')             #18
label('v6502_tsx')
ld(-20/2)                       #19
#
#label('v6502_tsx')
#nop()                          #12 Overlap
ld([v6502_S])                   #13
suba(1)                         #14 Shift down on export
st([v6502_X])                   #15
label('.tsx16')
st([v6502_Qz])                  #16 Z flag
st([v6502_Qn])                  #17 N flag
nop()                           #18
ld(hi('v6502_next'),Y)          #19
jmp(Y,'v6502_next')             #20
ld(-22/2)                       #21

label('v6502_txs')
ld([v6502_X])                   #12
adda(1)                         #13 Shift up on import
bra('.tsx16')                   #14
st([v6502_S])                   #15

label('v6502_tay')
ld([v6502_A])                   #12
bra('.tax15')                   #13
st([v6502_Y])                   #14

label('v6502_txa')
ld([v6502_X])                   #12
bra('.tax15')                   #13
st([v6502_A])                   #14

label('v6502_tya')
ld([v6502_Y])                   #12
bra('.tax15')                   #13
st([v6502_A])                   #14

label('v6502_cli')
ld([v6502_P])                   #12
bra('.clv15')                   #13
anda(~v6502_Iflag)              #14

label('v6502_sei')
ld([v6502_P])                   #12
bra('.clv15')                   #13
ora(v6502_Iflag)                #14

label('v6502_cld')
ld([v6502_P])                   #12
bra('.clv15')                   #13
anda(~v6502_Dflag)              #14

label('v6502_sed')
ld([v6502_P])                   #12
bra('.clv15')                   #13
label('v6502_clv')
ora(v6502_Dflag)                #14,12 Overlap
#
#label('v6502_clv')
#nop()                          #12
ld([v6502_P])                   #13
anda(~v6502_Vemu)               #14
label('.clv15')
st([v6502_P])                   #15
ld(hi('v6502_next'),Y)          #16
ld(-20/2)                       #17
jmp(Y,'v6502_next')             #18
label('v6502_bit')
nop()                           #19,12
#
#label('v6502_bit')
#nop()                          #12 Overlap
ld([v6502_ADL],X)               #13
ld([v6502_ADH],Y)               #14
ld([Y,X])                       #15
st([v6502_Qn])                  #16 N flag
anda([v6502_A])                 #17 This is a reason we keep N and Z in separate bytes
st([v6502_Qz])                  #18 Z flag
ld([v6502_P])                   #19
anda(~v6502_Vemu)               #20
st([v6502_P])                   #21
ld([Y,X])                       #22
adda(AC)                        #23
anda(v6502_Vemu)                #24
ora([v6502_P])                  #25
st([v6502_P])                   #26 Update V
ld(hi('v6502_next'),Y)          #27
jmp(Y,'v6502_next')             #28
ld(-30/2)                       #29

label('v6502_rts')
ld([v6502_S])                   #12
ld(AC,X)                        #13
adda(2)                         #14
st([v6502_S])                   #15
ld(0,Y)                         #16
ld([Y,X])                       #17
st([Y,Xpp])                     #18 Just X++
adda(1)                         #19
st([v6502_PCL])                 #20
beq(pc()+3)                     #21
bra(pc()+3)                     #22
ld(0)                           #23
ld(1)                           #23(!)
adda([Y,X])                     #24
st([v6502_PCH])                 #25
nop()                           #26
ld(hi('v6502_next'),Y)          #27
jmp(Y,'v6502_next')             #28
ld(-30/2)                       #29

label('v6502_php')
ld([v6502_S])                   #12
suba(1)                         #13
st([v6502_S],X)                 #14
ld([v6502_P])                   #15
anda(~v6502_Vflag&~v6502_Zflag) #16 Keep Vemu,B,D,I,C
bpl(pc()+3)                     #17 V to bit 6 and clear N
bra(pc()+2)                     #18
xora(v6502_Vflag^v6502_Vemu)    #19
st([X])                         #19,20
ld([v6502_Qz])                  #21 Z flag
beq(pc()+3)                     #22
bra(pc()+3)                     #23
ld(0)                           #24
ld(v6502_Zflag)                 #24(!)
ora([X])                        #25
st([X])                         #26
ld([v6502_Qn])                  #27 N flag
anda(0x80)                      #28
ora([X])                        #29
ora(v6502_Uflag)                #30 Unused bit
st([X])                         #31
nop()                           #32
ld(hi('v6502_next'),Y)          #33
jmp(Y,'v6502_next')             #34
ld(-36/2)                       #35

label('v6502_cpx')
bra('.cmp14')                   #12
ld([v6502_X])                   #13

label('v6502_cpy')
bra('.cmp14')                   #12
label('v6502_cmp')
ld([v6502_Y])                   #13,12
#
#label('v6502_cmp')             #12 Overlap
assert v6502_Cflag == 1
ld([v6502_A])                   #13
label('.cmp14')
ld([v6502_ADH],Y)               #14
bmi('.cmp17')                   #15 Carry?
suba([Y,X])                     #16
st([v6502_Qz])                  #17 Z flag
st([v6502_Qn])                  #18 N flag
bra('.cmp21')                   #19
ora([Y,X])                      #20
label('.cmp17')
st([v6502_Qz])                  #17 Z flag
st([v6502_Qn])                  #18 N flag
anda([Y,X])                     #19
nop()                           #20
label('.cmp21')
xora(0x80)                      #21
anda(0x80,X)                    #22 Move carry to bit 0
ld([v6502_P])                   #23 C flag
anda(~1)                        #24
ora([X])                        #25
st([v6502_P])                   #26
ld(hi('v6502_next'),Y)          #27
jmp(Y,'v6502_next')             #28
ld(-30/2)                       #29

label('v6502_plp')
assert v6502_Nflag == 128
assert 2*v6502_Vflag == v6502_Vemu
ld([v6502_S])                   #12
ld(AC,X)                        #13
adda(1)                         #14
st([v6502_S])                   #15
ld([X])                         #16
st([v6502_Qn])                  #17 N flag
anda(v6502_Zflag)               #18
xora(v6502_Zflag)               #19
st([v6502_Qz])                  #20 Z flag
ld([X])                         #21
anda(~v6502_Vemu)               #22 V to bit 7
adda(v6502_Vflag)               #23
st([v6502_P])                   #24 All other flags
ld(hi('v6502_next'),Y)          #25
jmp(Y,'v6502_next')             #26
ld(-28/2)                       #27

label('v6502_rti')
ld([v6502_S])                   #12
ld(AC,X)                        #13
adda(3)                         #14
st([v6502_S])                   #15
ld([X])                         #16
st([v6502_Qn])                  #17 N flag
anda(v6502_Zflag)               #18
xora(v6502_Zflag)               #19
st([v6502_Qz])                  #20 Z flag
ld(0,Y)                         #21
ld([Y,X])                       #22
st([Y,Xpp])                     #23 Just X++
anda(~v6502_Vemu)               #24 V to bit 7
adda(v6502_Vflag)               #25
st([v6502_P])                   #26 All other flags
ld([Y,X])                       #27
st([Y,Xpp])                     #28 Just X++
st([v6502_PCL])                 #29
ld([Y,X])                       #30
st([v6502_PCH])                 #31
nop()                           #32
ld(hi('v6502_next'),Y)          #33
jmp(Y,'v6502_next')             #34
ld(-36/2)                       #35


#-----------------------------------------------------------------------
#
#  $1200 ROM page 18: Extended vbl & SYS calls
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

#-----------------------------------------------------------------------
#       Extended vertical blank logic: interrupts
#-----------------------------------------------------------------------

# Manual runVcpu with vReturn already set
label('vBlankFirst#vCPU1')      # with halfTick
st(0,[0])
label('vBlankFirst#vCPU0')      # witout halfTick
ld([vCpuSelect],Y)
jmp(Y,'ENTER')
nop()

# IRQ logic
label('vBlankFirst#77')
ld([Y,vIRQ_v5])                 #77 check if there is a irq handler
ora([Y,vIRQ_v5+1])              #78
n,m = runVcpu_ticks(190-79-extra, 5, '---D line 0 timeout no irq')
beq('vBlankFirst#vCPU%d' % m)   #79
ld(n)                           #80

ld([Y, vIrqCtx_v7])             #81 check if ctx-style irq
bne('vBlankFirst#84')           #82
ld([vPC])                       #83
st([vIrqSave+0])                #84 Save vPC
ld([vPC+1])                     #85
st([vIrqSave+1])                #86
ld([vAC])                       #87 Save vAC
st([vIrqSave+2])                #88
ld([vAC+1])                     #89
st([vIrqSave+3])                #90
ld([vCpuSelect])                #91 Save vCpuSelect
st([vIrqSave+4])                #92
ld([Y,vIRQ_v5])                 #93 Set vPC to vIRQ
suba(2)                         #94
st([vPC])                       #95
ld([Y,vIRQ_v5+1])               #96
st([vPC+1])                     #97
ld(hi('ENTER'))                 #98 Set vCpuSelect to ENTER (=regular vCPU)
st([vCpuSelect])                #99
n,m = runVcpu_ticks(190-100-extra, 5, '---D line 0 timeout std irq')
bra('vBlankFirst#vCPU%d' % m)   #100
ld(n)                           #101

label('vBlankFirst#84')
ld([Y, vIrqCtx_v7])             #84
ld(AC,Y)                        #85 
ld([Y,0xff])                    #86 irqMask
beq('vBlankFirst#89')           #87
st([Y,0xfe])                    #88 irqFlag
n,m = runVcpu_ticks(190-89-extra, 5, '---D line 0 timeout masked irq')
bra('vBlankFirst#vCPU%d' % m)   #89 
ld(n)

label('vBlankFirst#89')
ld(hi('vIRQ#92'),Y)             #89 ctx irq
jmp(Y,'vIRQ#92')                #90
ld(hi(vIrqCtx_v7),Y)            #91

#-----------------------------------------------------------------------
#       Extended vertical blank logic: game controller decoding
#-----------------------------------------------------------------------

# Entered last line of vertical blank (line 40)
label('vBlankLast#34')

# Game controller types
# TypeA: Based on 74LS165 shift register (not supported)
# TypeB: Based on CD4021B shift register (standard)
# TypeC: Based on priority encoder
#
# Notes:
# - TypeA was only used during development and first beta test, before ROM v1
# - TypeB appears as type A with negative logic levels
# - TypeB is the game controller type that comes with the original kit and ROM v1
# - TypeB is mimicked by BabelFish / Pluggy McPlugface
# - TypeB requires a prolonged /SER_LATCH, therefore vPulse is 8 scanlines, not 2
# - TypeB and TypeC can be sampled in the same scanline
# - TypeA is 1 scanline shifted as it looks at a different edge (XXX up or down?)
# - TypeC gives incomplete information: lower buttons overshadow higher ones
#
#       TypeC    Alias    Button TypeB
#       00000000  ^@   -> Right  11111110
#       00000001  ^A   -> Left   11111101
#       00000011  ^C   -> Down   11111011
#       00000111  ^G   -> Up     11110111
#       00001111  ^O   -> Start  11101111
#       00011111  ^_   -> Select 11011111
#       00111111  ?    -> B      10111111
#       01111111  DEL  -> A      01111111
#       11111111       -> (None) 11111111
#
#       Conversion formula:
#               f(x) := 254 - x

# Detect controller TypeC codes
ld([serialRaw])                 #34 if serialRaw in [0,1,3,7,15,31,63,127,255]
adda(1)                         #35
anda([serialRaw])               #36
bne('.buttons#39')              #37

# TypeC
ld([serialRaw])                 #38 [TypeC] if serialRaw < serialLast
adda(1)                         #39
anda([serialLast])              #40
bne('.buttons#43')              #41
ld(254)                         #42 then clear the selected bit
nop()                           #43
bra('.buttons#46')              #44
label('.buttons#43')
suba([serialRaw])               #43,45
anda([buttonState])             #44
st([buttonState])               #45
label('.buttons#46')
ld([serialRaw])                 #46 Set the lower bits
ora([buttonState])              #47
label('.buttons#48')
st([buttonState])               #48
ld([serialRaw])                 #49 Update serialLast for next pass
jmp(Y,'vBlankLast#52')          #50
st([serialLast])                #51

# TypeB
# pChange = pNew & ~pOld
# nChange = nNew | ~nOld {DeMorgan}
label('.buttons#39')
ld(255)                         #39 [TypeB] Bitwise edge-filter to detect button presses
xora([serialLast])              #40
ora([serialRaw])                #41 Catch button-press events
anda([buttonState])             #42 Keep active button presses
ora([serialRaw])                #43
nop()                           #44
nop()                           #45
bra('.buttons#48')              #46
nop()                           #47


#-----------------------------------------------------------------------
#       More SYS functions
#-----------------------------------------------------------------------

# SYS_VDrawBits_134 implementation
label('sys_VDrawBits')
ld(0)                           #18
label('.sysVdb0')
st([vTmp])                      #19+i*12
adda([sysArgs+5],Y)             #20+i*12 Y=[sysPos+1]+[vTmp]
ld([sysArgs+2])                 #21+i*12 Select color
bmi('.sysVdb1')                 #22+i*12
adda(AC)                        #23+i*12
st([sysArgs+2])                 #24+i*12
ld([sysArgs+0])                 #25+i*12
st([Y,X])                       #26+i*12
ld([vTmp])                      #27+i*12
suba(7)                         #28+i*12
bne('.sysVdb0')                 #29+i*12
adda(8)                         #30+i*12
ld(hi('REENTER'),Y)             #115
jmp(Y,'REENTER')                #116
ld(-120/2)                      #117
label('.sysVdb1')
st([sysArgs+2])                 #24+i*12
ld([sysArgs+1])                 #25+i*12
st([Y,X])                       #26+i*12
ld([vTmp])                      #27+i*12
suba(7)                         #28+i*12
bne('.sysVdb0')                 #29+i*12
adda(8)                         #30+i*12
ld(hi('REENTER'),Y)             #115
jmp(Y,'REENTER')                #116
ld(-120/2)                      #117

# SYS_ResetWaveforms_v4_50 implementation
label('sys_ResetWaveforms')
ld([vAC+0])                     #18 X=4i
adda(AC)                        #19
adda(AC,X)                      #20
ld([vAC+0])                     #21
st([Y,Xpp])                     #22 Sawtooth: T[4i+0] = i
anda(0x20)                      #23 Triangle: T[4i+1] = 2i if i<32 else 127-2i
bne(pc()+3)                     #24
ld([vAC+0])                     #25
bra(pc()+3)                     #26
adda([vAC+0])                   #26,27
xora(127)                       #27
st([Y,Xpp])                     #28
ld([vAC+0])                     #29 Pulse: T[4i+2] = 0 if i<32 else 63
anda(0x20)                      #30
bne(pc()+3)                     #31
bra(pc()+3)                     #32
ld(0)                           #33
ld(63)                          #33(!)
st([Y,Xpp])                     #34
ld([vAC+0])                     #35 Sawtooth: T[4i+3] = i
st([Y,X])                       #36
adda(1)                         #37 i += 1
st([vAC+0])                     #38
xora(64)                        #39 For 64 iterations
beq(pc()+3)                     #40
bra(pc()+3)                     #41
ld(-2)                          #42
ld(0)                           #42(!)
adda([vPC])                     #43
st([vPC])                       #44
ld(hi('REENTER'),Y)             #45
jmp(Y,'REENTER')                #46
ld(-50/2)                       #47

# SYS_ShuffleNoise_v4_46 implementation
label('sys_ShuffleNoise')
ld([vAC+0],X)                   #18 tmp = T[4j]
ld([Y,X])                       #19
st([vTmp])                      #20
ld([vAC+1],X)                   #21 T[4j] = T[4i]
ld([Y,X])                       #22
ld([vAC+0],X)                   #23
st([Y,X])                       #24
adda(AC)                        #25 j += T[4i]
adda(AC,)                       #26
adda([vAC+0])                   #27
st([vAC+0])                     #28
ld([vAC+1],X)                   #29 T[4i] = tmp
ld([vTmp])                      #30
st([Y,X])                       #31
ld([vAC+1])                     #32 i += 1
adda(4)                         #33
st([vAC+1])                     #34
beq(pc()+3)                     #35 For 64 iterations
bra(pc()+3)                     #36
ld(-2)                          #37
ld(0)                           #37(!)
adda([vPC])                     #38
st([vPC])                       #39
ld(hi('NEXTY'),Y)               #40
jmp(Y,'NEXTY')                  #41
ld(-44/2)                       #42


#----------------------------------------
# SYS_ScanMemory{Ext}

# SYS_ScanMemory_DEVROM_50 implementation
label('sys_ScanMemory')
ld([sysArgs+0],X)                    #18
ld([Y,X])                            #19
label('.sysSme#20')
xora([sysArgs+2])                    #20
beq('.sysSme#23')                    #21
ld([Y,X])                            #22
xora([sysArgs+3])                    #23
beq('.sysSme#26')                    #24
ld([sysArgs+0])                      #25
adda(1);                             #26
st([sysArgs+0],X)                    #27
ld([vAC])                            #28
suba(1)                              #29
beq('.sysSme#32')                    #30 return zero
st([vAC])                            #31
ld(-18/2)                            #14 = 32 - 18
adda([vTicks])                       #15
st([vTicks])                         #16
adda(min(0,maxTicks -(28+18)/2))     #17
bge('.sysSme#20')                    #18
ld([Y,X])                            #19
ld(-2)                               #20 restart
adda([vPC])                          #21
st([vPC])                            #22
ld(hi('REENTER'),Y)                  #23
jmp(Y,'REENTER')                     #24
ld(-28/2)                            #25
label('.sysSme#32')
st([vAC+1])                          #32 return zero
ld(hi('REENTER'),Y)                  #33
jmp(Y,'REENTER')                     #34
ld(-38/2)                            #35
label('.sysSme#23')
nop()                                #23 success
nop()                                #24
ld([sysArgs+0])                      #25
label('.sysSme#26')
st([vAC])                            #26 success
ld([sysArgs+1])                      #27
st([vAC+1])                          #28
ld(hi('REENTER'),Y)                  #29
jmp(Y,'REENTER')                     #30
ld(-34/2)                            #31

# SYS_ScanMemoryExt_DEVROM_50 implementation
label('sys_ScanMemoryExt')
ora(0x3c,X)                          #18
ctrl(X)                              #19
ld([sysArgs+1],Y)                    #20
ld([sysArgs+0],X)                    #21
ld([Y,X])                            #22
nop()                                #23
label('.sysSmx#24')
xora([sysArgs+2])                    #24
beq('.sysSmx#27')                    #25
ld([Y,X])                            #26
xora([sysArgs+3])                    #27
beq('.sysSmx#30')                    #28
ld([sysArgs+0])                      #29
adda(1);                             #30
st([sysArgs+0],X)                    #31
ld([vAC])                            #32
suba(1)                              #33
beq('.sysSmx#36')                    #34 return zero
st([vAC])                            #35
ld(-18/2)                            #18 = 36 - 18
adda([vTicks])                       #19
st([vTicks])                         #20
adda(min(0,maxTicks -(30+18)/2))     #21
bge('.sysSmx#24')                    #22
ld([Y,X])                            #23
ld([vPC])                            #24
suba(2)                              #25 restart
st([vPC])                            #26
ld(hi(ctrlBits),Y)                   #27 restore and return
ld([Y,ctrlBits])                     #28
anda(0xfc,X)                         #29
ctrl(X)                              #30
ld([vTmp])                           #31
ld(hi('NEXTY'),Y)                    #32
jmp(Y,'NEXTY')                       #33
ld(-36/2)                            #34
label('.sysSmx#27')
nop()                                #27 success
nop()                                #28
ld([sysArgs+0])                      #29
label('.sysSmx#30')
st([vAC])                            #30 success
ld([sysArgs+1])                      #31
nop()                                #32
nop()                                #33
nop()                                #34
nop()                                #35
label('.sysSmx#36')
st([vAC+1])                          #36
ld(hi(ctrlBits),Y)                   #37 restore and return
ld([Y,ctrlBits])                     #38
anda(0xfc,X)                         #39
ctrl(X)                              #40
ld([vTmp])                           #41
ld(hi('NEXTY'),Y)                    #42
jmp(Y,'NEXTY')                       #43
ld(-46/2)                            #44


#-----------------------------------------------------------------------
#
#  $1300 ROM page 19: SYS calls
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

# SYS_CopyMemory_v6_80 implementation

label('sys_CopyMemory')
ble('.sysCm#20')                     #18   goto burst6
suba(6)                              #19
bge('.sysCm#22')                     #20   goto burst6
ld([sysArgs+3],Y)                    #21
adda(3)                              #22
bge('.sysCm#25')                     #23   goto burst3
ld([sysArgs+2],X)                    #24

adda(2)                              #25   single
st([vAC])                            #26
ld([Y,X])                            #27
ld([sysArgs+1],Y)                    #28
ld([sysArgs+0],X)                    #29
st([Y,X])                            #30
ld([sysArgs+0])                      #31
adda(1)                              #32
st([sysArgs+0])                      #33
ld([sysArgs+2])                      #34
adda(1)                              #35
st([sysArgs+2])                      #36
ld([vAC])                            #37
beq(pc()+3)                          #38
bra(pc()+3)                          #39
ld(-2)                               #40
ld(0)                                #40!
adda([vPC])                          #41
st([vPC])                            #42
ld(hi('REENTER'),Y)                  #43
jmp(Y,'REENTER')                     #44
ld(-48/2)                            #45

label('.sysCm#25')
st([vAC])                            #25   burst3
for i in range(3):
  ld([Y,X])                            #26+3*i
  st([sysArgs+4+i])                    #27+3*i
  st([Y,Xpp]) if i<2 else None         #28+3*i
ld([sysArgs+1],Y)                    #34
ld([sysArgs+0],X)                    #35
for i in range(3):
  ld([sysArgs+4+i])                    #36+2*i
  st([Y,Xpp])                          #37+2*i
ld([sysArgs+0])                      #42
adda(3)                              #43
st([sysArgs+0])                      #44
ld([sysArgs+2])                      #45
adda(3)                              #46
st([sysArgs+2])                      #47
ld([vAC])                            #48
beq(pc()+3)                          #49
bra(pc()+3)                          #50
ld(-2)                               #51
ld(0)                                #51!
adda([vPC])                          #52
st([vPC])                            #53
ld(hi('NEXTY'),Y)                    #54
jmp(Y,'NEXTY')                       #55
ld(-58/2)                            #56

label('.sysCm#20')
nop()                                #20   burst6
ld([sysArgs+3],Y)                    #21
label('.sysCm#22')
st([vAC])                            #22   burst6
ld([sysArgs+2],X)                    #23
for i in range(6):
  ld([Y,X])                            #24+i*3
  st([vLR+i if i<2 else sysArgs+2+i])  #25+i*3
  st([Y,Xpp]) if i<5 else None         #26+i*3 if i<5
ld([sysArgs+1],Y)                    #41
ld([sysArgs+0],X)                    #42
for i in range(6):
  ld([vLR+i if i<2 else sysArgs+2+i])  #43+i*2
  st([Y,Xpp])                          #44+i*2
ld([sysArgs+0])                      #55
adda(6)                              #56
st([sysArgs+0])                      #57
ld([sysArgs+2])                      #58
adda(6)                              #59
st([sysArgs+2])                      #60

ld([vAC])                            #61
bne('.sysCm#64')                     #62
ld(hi('REENTER'),Y)                  #63
jmp(Y,'REENTER')                     #64
ld(-68/2)                            #65

label('.sysCm#64')
ld(-52/2)                            #64
adda([vTicks])                       #13 = 65 - 52
st([vTicks])                         #14
adda(min(0,maxTicks-(26+52)/2))      #15
bge('sys_CopyMemory')                #16 self-dispatch
ld([vAC])                            #17
ld(-2)                               #18 restart
adda([vPC])                          #19
st([vPC])                            #20
ld(hi('REENTER'),Y)                  #21
jmp(Y,'REENTER')                     #22
ld(-26/2)                            #23

#----------------------------------------
# SYS_CopyMemoryExt_v6_100 implementation

label('sys_CopyMemoryExt')

adda(AC)                             #18
adda(AC)                             #19
ora(0x3c)                            #20
st([vTmp])                           #21 [vTmp] = src ctrl value
ld([vAC+1])                          #22
anda(0xfc)                           #23
ora(0x3c)                            #24
st([vLR])                            #25 [vLR] = dest ctrl value

label('.sysCme#26')
ld([vAC])                            #26
ble('.sysCme#29')                    #27   goto burst5
suba(5)                              #28
bge('.sysCme#31')                    #29   goto burst5
ld([sysArgs+3],Y)                    #30
adda(4)                              #31

st([vAC])                            #32   single
ld([vTmp],X)                         #33
ctrl(X)                              #34
ld([sysArgs+2],X)                    #35
ld([Y,X])                            #36
ld([vLR],X)                          #37
ctrl(X)                              #38
ld([sysArgs+1],Y)                    #39
ld([sysArgs+0],X)                    #40
st([Y,X])                            #41
ld(hi(ctrlBits), Y)                  #42
ld([Y,ctrlBits])                     #43
ld(AC,X)                             #44
ctrl(X)                              #45
ld([sysArgs+0])                      #46
adda(1)                              #47
st([sysArgs+0])                      #48
ld([sysArgs+2])                      #49
adda(1)                              #50
st([sysArgs+2])                      #51
ld([vAC])                            #52  done?
beq(pc()+3)                          #53
bra(pc()+3)                          #54
ld(-2)                               #55  restart
ld(0)                                #55! finished
adda([vPC])                          #56
st([vPC])                            #57
ld(hi('NEXTY'),Y)                    #58
jmp(Y,'NEXTY')                       #59
ld(-62/2)                            #60

label('.sysCme#29')
nop()                                #29   burst5
ld([sysArgs+3],Y)                    #30
label('.sysCme#31')
st([vAC])                            #31   burst5
ld([vTmp],X)                         #32
ctrl(X)                              #33
ld([sysArgs+2],X)                    #34
for i in range(5):
  ld([Y,X])                            #35+i*3
  st([vLR+1 if i<1 else sysArgs+3+i])  #36+i*3
  st([Y,Xpp]) if i<4 else None         #37+i*3 if i<4
ld([vLR],X)                          #49
ctrl(X)                              #50
ld([sysArgs+1],Y)                    #51
ld([sysArgs+0],X)                    #52
for i in range(5):
  ld([vLR+1 if i<1 else sysArgs+3+i])  #53+i*2
  st([Y,Xpp])                          #54+i*2
ld([sysArgs+0])                      #63
adda(5)                              #64
st([sysArgs+0])                      #65
ld([sysArgs+2])                      #66
adda(5)                              #67
st([sysArgs+2])                      #68

ld([vAC])                            #69
bne('.sysCme#72')                    #70
ld(hi(ctrlBits), Y)                  #71  we're done!
ld([Y,ctrlBits])                     #72
anda(0xfc,X)                         #73
ctrl(X)                              #74
ld([vTmp])                           #75  always read after ctrl
ld(hi('NEXTY'),Y)                    #76
jmp(Y,'NEXTY')                       #77
ld(-80/2)                            #78

label('.sysCme#72')
ld(-52/2)                            #72
adda([vTicks])                       #21 = 72 - 52
st([vTicks])                         #22
adda(min(0,maxTicks-(40+52)/2))      #23
bge('.sysCme#26')                    #24  enough time for another loop
ld(-2)                               #25
adda([vPC])                          #26  restart
st([vPC])                            #27
ld(hi(ctrlBits), Y)                  #28
ld([Y,ctrlBits])                     #29
anda(0xfc,X)                         #30
ctrl(X)                              #31
ld([vTmp])                           #32 always read after ctrl
ld(hi('REENTER'),Y)                  #33
jmp(Y,'REENTER')                     #34
ld(-38/2)                            #35 max: 38 + 52 = 90 cycles


#----------------------------------------
# SYS_Mutiply / SYS_Divide fsm entry

# sys_Multiply_s16 (page 0x14)
label('sys_Multiply_s16')
ld('sysm#3a')                   #18
st([fsmState])                  #19
ld(1)                           #20
st([sysArgs+6])                 #21
ld(hi('FSM14_ENTER'))           #22 jump into multiply fsm
st([vCpuSelect])                #23
nop()                           #24
adda(1,Y)                       #25
jmp(Y,'NEXT')                   #26
ld(-28/2)                       #27

# sys_Divide_u16 (page 0x14)
label('sys_Divide_u16')
ld('sysd#3a')                   #18
st([fsmState])                  #19
ld(0)                           #20 init
st([sysArgs+4])                 #21
st([sysArgs+5])                 #22
ld(15*8)                        #23
st([sysArgs+6])                 #24
ld(hi('FSM14_ENTER'))           #25 jump into divide fsm
st([vCpuSelect])                #26
adda(1,Y)                       #27
jmp(Y, 'NEXT')                  #28
ld(-30/2)                       #29




#-----------------------------------------------------------------------
#
#  $1400 ROM page 20: Multiply Divide
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM14_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM14_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8


#-----------------------------------------------------------------------
# Multiplication machine (signed or unsigned)
# sum += x * y
# x:sysArgs[01] y:sysArgs[23]
# sum: sysArgs[45]
# mask: sysArgs[6] must be 1

label('sysm#3a')
ld('sysm#3b')                   #3
st([fsmState])                  #4
ld([sysArgs+6])                 #5
anda([sysArgs+2])               #6
nop()                           #7
beq('NEXT')                     #8
ld(-10/2)                       #9
ld([sysArgs+4])                 #10 load sum.lo
adda([sysArgs+0])               #11 load x.lo
st([sysArgs+4])                 #12 sum.lo = sum.lo + x.lo
bmi(pc()+4)                     #13 check for carry
suba([sysArgs+0])               #14 get original sum.lo back
bra(pc()+4)                     #15
ora([sysArgs+0])                #16 carry in bit 7
nop()                           #15
anda([sysArgs+0])               #16 carry in bit 7
anda(0x80,X)                    #17
ld([X])                         #18
adda([sysArgs+5])               #19
adda([sysArgs+1])               #20
st([sysArgs+5])                 #21 sum.hi = sum.hi + x.hi
bra('NEXT')                     #22
ld(-24/2)                       #23

label('sysm#3b')
ld([sysArgs+0])                 #3  AC = x.lo
anda(0x80,X)                    #4  X = AC & 0x80
adda(AC)                        #5  AC = x.lo <<1
st([sysArgs+0])                 #6  x.lo = AC
ld([X])                         #7  AC = X >>7
adda([sysArgs+1])               #8
adda([sysArgs+1])               #9
st([sysArgs+1])                 #10 x.hi = x.hi <<1 + AC
ld([sysArgs+6])                 #11
adda([sysArgs+6])               #12
beq('sysm#15b')                 #13
st([sysArgs+6])                 #14
ld('sysm#3a')                   #15
st([fsmState])                  #16
nop()
bra('NEXT')                     #17
ld(-20/2)                       #18
label('sysm#15b')
ld([sysArgs+3])                 #15
beq(pc()+3)                     #16
bra(pc()+2)                     #17
ld(1)                           #18
st([sysArgs+6])                 #19,18
ld('sysm#3c')                   #20
st([fsmState])                  #21
bra('NEXT')                     #22
ld(-24/2)                       #23

label('sysm#3c')
ld([sysArgs+6])                 #3
beq('sysm#6c')                  #4
anda([sysArgs+3])               #5
beq('sysm#8c')                  #6
ld([sysArgs+1])                 #7 add
adda([sysArgs+5])               #8
st([sysArgs+5])                 #9
label('sysm#10c')
ld([sysArgs+1])                 #10
adda(AC)                        #11
st([sysArgs+1])                 #12
ld([sysArgs+6])                 #13
adda(AC)                        #14
st([sysArgs+6])                 #15
bra('NEXT')                     #16
ld(-18/2)                       #17
label('sysm#8c')
bra('sysm#10c')                 #8  no add
nop()                           #9
label('sysm#6c')
ld([sysArgs+4])                 #6  exit
st([vAC])                       #7
ld([sysArgs+5])                 #8
st([vAC+1])                     #9
ld(hi('ENTER'))                 #10
st([vCpuSelect])                #11
ld(hi('NEXTY'),Y)               #12
jmp(Y,'NEXTY')                  #13
ld(-16//2)                      #14


#-----------------------------------------------------------------------
# Division machine (mostly unsigned)
# - sysArgs[01] is the dividend, contains the quotient on output
# - sysArgs[23] is the divisor
# - sysArgs[45] must be zero, contains the remainder on output
# - sysArgs[6] must be 0x011110xy on input
#     if x is 1, remainder will be negated
#     if y is 1, quotient will bw negated

label('sysd#3a')
ld('sysd#3b')                   #3
st([fsmState])                  #4
ld([sysArgs+0])                 #5  lsl sysArgs5<4<1<0
anda(0x80,X)                    #6
adda(AC)                        #7
st([sysArgs+0])                 #8
ld([sysArgs+1])                 #9
bmi('sysd#12a')                 #10
adda(AC)                        #11
adda([X])                       #12
st([sysArgs+1])                 #13
ld([sysArgs+4])                 #14
anda(0x80,X)                    #15
bra('sysd#18a')                 #16
adda(AC)                        #17
label('sysd#12a')
adda([X])                       #12
st([sysArgs+1])                 #13
ld([sysArgs+4])                 #14
anda(0x80,X)                    #15
adda(AC)                        #16
adda(1)                         #17
label('sysd#18a')
st([sysArgs+4])                 #18
ld([sysArgs+5])                 #19
adda(AC)                        #20
adda([X])                       #21
st([sysArgs+5])                 #22
nop()                           #23
bra('NEXT')                     #24
ld(-26/2)                       #25

label('sysd#3b')
ld([sysArgs+4])                 #3 vAC=sysArgs[45]-sysArgs[23]
bmi(pc()+5)                     #4>
suba([sysArgs+2])               #5
st([vAC])                       #6
bra(pc()+5)                     #7>
ora([sysArgs+2])                #8
st([vAC])                       #6-
nop()                           #7
anda([sysArgs+2])               #8
anda(0x80,X)                    #9-
ld([sysArgs+5])                 #10
bmi('sysd#13b')                 #11
suba([sysArgs+3])               #12
suba([X])                       #13
st([vAC+1])                     #14
ora([sysArgs+3])                #15
bmi('sysd#19bd')                #16
bra('sysd#19b')                 #17
label('sysd#19bc')
ld('sysd#3c')                   #18
label('sysd#13b')
suba([X])                       #13
st([vAC+1])                     #14
anda([sysArgs+3])               #15
bpl('sysd#19bc')                #16
bra('sysd#19b')                 #17
label('sysd#19bd')
ld('sysd#3d')                   #18
label('sysd#19b')
st([fsmState])                  #19
bra('NEXT')                     #20
ld(-22/2)                       #21

label('sysd#3c')
ld([sysArgs+0])                 #3 commit
ora(1)                          #4  quotient|=1
st([sysArgs+0])                 #5
ld([vAC])                       #6  sysArgs[45]=vAC
st([sysArgs+4])                 #7
ld([vAC+1])                     #8
st([sysArgs+5])                 #9
ld([sysArgs+6])                 #10 counter
suba(8)                         #11
blt('sysd#14c')                 #12
st([sysArgs+6])                 #13
ld('sysd#3a')                   #14
st([fsmState])                  #15
bra('NEXT')                     #16
ld(-18/2)                       #17
label('sysd#14c')
ld('sysd#3e')                   #14
st([fsmState])                  #15
bra('NEXT')                     #16
ld(-18/2)                       #17

label('sysd#3d')
ld('sysd#3a')                   #3
st([fsmState])                  #4
ld([sysArgs+6])                 #5 counter
suba(8)                         #6
st([sysArgs+6])                 #7
bge('NEXT')                     #8
ld(-10/2)                       #9
ld('sysd#3e')                   #10
st([fsmState])                  #11
bra('NEXT')                     #12
ld(-14/2)                       #13

label('sysd#3e')
ld([sysArgs+6])                 #3
anda(3)                         #4
beq('sysd#7e')                  #5
anda(1)                         #6
bne('rdivs#9b')                 #7 neg quotient if [sysArgs+6]&1
ld(sysArgs+0,X)                 #8
st([sysArgs+6],Y)               #9 neg remainder if [sysArgs+6]&2
bra('rdivs#12b')                #10
ld(sysArgs+4,X)                 #11
label('sysd#7e')
ld([sysArgs+0])                 #7 copy quotient into vAC
st([vAC])                       #8
ld([sysArgs+1])                 #9
st([vAC+1])                     #10
ld(hi('ENTER'))                 #11 exit fsm
st([vCpuSelect])                #12
ld(hi('REENTER'),Y)             #13
jmp(Y,'REENTER')                #14
ld(-18//2)                      #15


#-----------------------------------------------------------------------
# FSM14 Opcodes

# MULW implementation
label('mulw#3a')
ld('sysm#3a')                   #3
st([fsmState])                  #4
ld(1)                           #5
nop()                           #6
label('mulw#7a')
st([vTmp])                      #7
ld([vAC])                       #8
st([sysArgs+2])                 #9
ld([vAC+1])                     #10
st([sysArgs+3])                 #11
ld([sysArgs+6])                 #12
adda(1,X)                       #13
ld([X])                         #14
st([sysArgs+1])                 #15
ld([sysArgs+6],X)               #16
ld([X])                         #17
st([sysArgs+0])                 #18
ld(0)                           #19
st([sysArgs+4])                 #20
st([sysArgs+5])                 #21
ld([vTmp])                      #22
st([sysArgs+6])                 #23
bra('NEXT')                     #24
ld(-26/2)                       #25

# RDIVU implementation
label('rdivu#3a')
ld('sysd#3a')                   #3
st([fsmState])                  #4
bra('mulw#7a')                  #5
ld(15*8)                        #6

# RDIVS implementation
label('rdivs#3a')
ld('rdivs#3b')                  #3
st([fsmState])                  #4
bra('mulw#7a')                  #5
ld(15*8)                        #6

label('rdivs#3b')
ld('rdivs#3c')                  #3
st([fsmState])                  #4
ld(sysArgs+2,X)                 #5
ld([sysArgs+3])                 #6 test divisor sign
bge('rdivs#9c')                 #7
ld(1)                           #8
label('rdivs#9b')
xora([sysArgs+6])               #9
st([sysArgs+6])                 #10
ld(0,Y)                         #11 negate [X]
label('rdivs#12b')
ld(0)                           #12
suba([Y,X])                     #13
st([Y,Xpp])                     #14
beq(pc()-3)                     #15 ld(0)
bra(pc()+2)                     #16
ld(0xff)                        #17
suba([Y,X])                     #18
st([Y,X])                       #19
bra('NEXT')                     #20
ld(-22/2)                       #21

label('rdivs#3c')
ld('sysd#3a')                   #3
st([fsmState])                  #4
ld(sysArgs+0,X)                 #5
ld([sysArgs+1])                 #6 test dividend sign
blt('rdivs#9b')                 #7
ld(3)                           #8
label('rdivs#9c')
nop()                           #9
bra('NEXT')                     #10
ld(-12/2)                       #11

#-----------------------------------------------------------------------
#
#  $1500 ROM page 21: SYS_Loader
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM15_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM15_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8

# Ensure labels defined here do not conflict
def fsmLab(n):
    return f'fsm15:{n}'

# Assemble u-opcode
def fsmAsm(op,arg=None):
    bra(fsmLab(op))
    ld(pc()+1) if arg is None else ld(arg)

# Usage fsmAsm('ST', arg)
# - [arg] := vACL
label(fsmLab('ST'))
ld(hi('fsmST#8'),Y)             #5
jmp(Y,'fsmST#8')                #6 + overlap

# Usage fsmAsm('LD', arg)
# - vACL = arg with arg=d or arg=[d]
label(fsmLab('LD'))
ld(hi('fsmOP#8'),Y)             #5,7
jmp(Y,'fsmOP#8')                #6 + overlap

# Usage fsmAsm('XOR', arg)
# - vACL += arg with arg=d or arg=[d]
label(fsmLab('XOR'))
ld(hi('fsmOP#8'),Y)             #5,7
jmp(Y,'fsmOP#8')                #6
xora([vAC])                     #7

# Usage fsmAsm('AND', arg)
# - vACL &= arg with arg=d or arg=[d]
label(fsmLab('AND'))
ld(hi('fsmOP#8'),Y)             #5
jmp(Y,'fsmOP#8')                #6
anda([vAC])                     #7

# Usage fsmAsm('BNZ', arg)
# - branch if [vACL] is nonzero
label(fsmLab('BNZ'))
ld(hi('fsmBNZ#8'),Y)            #5
jmp(Y,'fsmBNZ#8')               #6
st([vTmp])                      #7

# Usage fsmAsm('B', arg)
# - unconditional branch
# - can be the same as BL is fsmLink can be trashed
label(fsmLab('B'))
st([fsmState])                  #5
bra('NEXT')                     #6
ld(-8/2)                        #7

# Usage: fsmAsm('VRETNZ')
# - if vLR is nonzero, return to vCPU at address vLR.
label(fsmLab('VRETNZ'))
ld(hi('fsmVRETNZ#8'),Y)         #5
jmp(Y,'fsmVRETNZ#8')            #6
st([fsmState])                  #7

# Usage: fsmAsm('ST+')
# - store vACL into [sysArgs23]
# - increment low address byte sysArgs2
# - decrements count sysArgs+4 and return it in vACL
label(fsmLab('ST+'))
ld(hi('fsmST+#8'),Y)            #5
jmp(Y,'fsmST+#8')               #6 + overlap

# Usage: fsmAsm('CHANMASK')
# - clear channelMask if segment [sysArgs[23],sysArgs[23]+sysArgs[4]]
#   overlaps OSCL/OSCH for audio channel 1-3
label(fsmLab('CHANMASK'))
ld(hi('fsmCHANMASK#8'),Y)       #5,7
jmp(Y,'fsmCHANMASK#8')          #6
st([fsmState])                  #7

# Usage: fsmAsm('SRIN')
# - get one serial byte
# - wait until videoY==sysArgs6 and save IN into vAC
# - increment sysArgs6 to the next payload scanline
label(fsmLab('SRIN'))
st([vTmp])                      #5
ld([sysArgs+6])                 #6
xora([videoY])                  #7
bne('NEXT')                     #8 restart until videoY==sysArgs0
ld(-10/2)                       #9
ld([vTmp])                      #10
st([fsmState])                  #11
ld([sysArgs+6])                 #12 next position
anda(1)                         #13 - even or odd?
bne('sl:srin#16')               #14
ld([sysArgs+6])                 #15
adda(4)                         #16 even
xora(242)                       #17
beq(pc()+3)                     #18
bra(pc()+3)                     #19
xora(242)                       #20
ld(185)                         #20!
bra('sl:srin#23')               #21
st([sysArgs+6])                 #22
label('sl:srin#16')
anda(0xf)                       #16 odd magic
adda([sysArgs+6])               #17
xora(4)                         #18
bpl(pc()+3)                     #19
bra(pc()+2)                     #20
ora(11)                         #21
st([sysArgs+6])                 #22,21
label('sl:srin#23')
st(IN,[vAC])                    #23 finally read byte
bra('NEXT')                     #24
ld(-26/2)                       #25

# Usage: fsmAsm('SLECHO')
# - handle loader echo on the screen
# - sysArgs0 is the x address, 0 to disable
# - sysArgs1 is the pixel row.
# - vAC the pixel color
label(fsmLab('SLECHO'))
st([fsmState])                  #5
ld([sysArgs+0])                 #6
ld(AC,X)                        #7
beq('sl:next#10')               #8
ld([sysArgs+1],Y)               #9
suba(11)                        #10
anda(127)                       #11
adda(12)                        #12
st([sysArgs+0])                 #13
ld([vAC])                       #14
st([Y,X])                       #15
ld([sysArgs+0],X)               #16
xora(0x3f)                      #17
bra('sl:next#20')               #18
st([Y,X])                       #19
label('sl:next#20')
bra('NEXT')                     #20
ld(-22/2)                       #21
label('sl:next#10')
bra('NEXT')                     #10
ld(-12/2)                       #11

# Usage: fsmAsm('SLCHK')
# - checks for loader program
label(fsmLab('SLCHK'))
st([fsmState])                  #5
ld([sysArgs+4])                 #6 len>60?
adda(67)                        #7
anda(0x80)                      #8
st([vAC])                       #9
ld([sysArgs+2])                 #10 writing echo area?
suba(0x20)                      #11
anda([sysArgs+2])               #12
anda(0x80,X)                    #13 X=0 [no] X=0x80 [maybe]
ld([sysArgs+3])                 #14
xora([sysArgs+1])               #15
ora([X])                        #16
bne(pc()-1)                     #17
bra('sl:next#20')               #18
st([sysArgs+0])                 #19

# Loader microprogram
label('sl:loader')
fsmAsm('LD', 0x15)              # echo color gray
label('sl:frame')
fsmAsm('SLECHO')
fsmAsm('LD', 207)
fsmAsm('ST', sysArgs+6)         # reset serial index
fsmAsm('SRIN')
fsmAsm('XOR', ord('L'))
fsmAsm('BNZ', 'sl:loader')      # invalid packet
fsmAsm('SRIN')
fsmAsm('AND', 0x3f)             # six valid bits only
fsmAsm('ST', sysArgs+4)         # len
fsmAsm('BNZ', 'sl:packet')
fsmAsm('SRIN')
fsmAsm('ST', vLR)               # execl
fsmAsm('SRIN')
fsmAsm('ST', vLR+1)             # exech
fsmAsm('VRETNZ')
label('sl:loop')
fsmAsm('B','sl:loop')
label('sl:packet')
fsmAsm('SRIN')
fsmAsm('ST', sysArgs+2)         # addrl
fsmAsm('SRIN')
fsmAsm('ST', sysArgs+3)         # addrh
fsmAsm('CHANMASK')
fsmAsm('SLCHK')                 # checks
fsmAsm('BNZ', 'sl:loader')      # invalid packet
label('sl:data')
fsmAsm('SRIN')
fsmAsm('ST+')
fsmAsm('BNZ', 'sl:data')
fsmAsm('LD', 0xc)              # next dot color
fsmAsm('B', 'sl:frame')

# Loader entry point
label('sys_Loader')
suba(12)                        #18
bge(pc()+3)                     #19
bra(pc()+3)                     #20
ld(0)                           #21
ld([sysArgs+0])                 #21
st([sysArgs+0])                 #22
ld('sl:loader')                 #23
st([fsmState])                  #24
ld(hi('FSM15_ENTER'))           #25
st([vCpuSelect])                #26
adda(1,Y)                       #27
jmp(Y,'NEXT')                   #28
ld(-30/2)                       #29

#----------------------------------------
# FSM micro-op implementation
# - callable from other FSMs because they return
#   to the running FSM with a jmp(Y,NEXT).

label('fsmST#8')
ld(AC,X)                        #8
ld([vAC])                       #9
st([X])                         #10
label('fsmST#11')
ld([fsmState])                  #11
adda(2)                         #12
label('fsmST#13')
st([fsmState])                  #13
label('fsmST#14')
ld([vCpuSelect])                #14
adda(1,Y)                       #15
jmp(Y,'NEXT')                   #16
ld(-18/2)                       #17

label('fsmOP#8')
st([vAC])                       #8
bra('fsmST#11')                 #9+overlap
nop()

label('fsmLSR4#8')
ld('fsmLSR4#19')                #9
st([vTmp])                      #10
ld([vAC])                       #11
anda(0xf0)                      #13
ora(0x7)                        #14
ld(hi('shiftTable'),Y)          #15
jmp(Y,AC)                       #14
bra(255)                        #15 continued in page 6

label('fsmBNZ#8')
ld([vAC])                       #8,10
beq('fsmST#11')                 #9
ld([vTmp])                      #10
bra('fsmST#13')                 #11+overlap
nop()

label('fsmBZ#8')
ld([vAC])                       #8
bne('fsmST#11')                 #9
ld([vTmp])                      #10
bra('fsmST#13')                 #11
nop()                           #12

label('fsmBL#8')
ld([fsmState])                  #8
adda(2)                         #9
st([sysArgs+6])                 #10
bra('fsmST#13')                 #11
ld([vTmp])                      #12

label('fsmVRETNZ#8')
ld([vLR])                       #8
ora([vLR+1])                    #9
beq('fsmVRETNZ#12')             #10
ld([vLR])                       #11
suba(2)                         #12
st([vPC])                       #13
ld([vLR+1])                     #14
st([vPC+1])                     #15
ld(hi('ENTER'))                 #16
st([vCpuSelect])                #17
adda(1,Y)                       #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20
label('fsmVRETNZ#12')
bra('fsmST#14' )                #12
nop()                           #13

label('fsmCHANMASK#8')
ld([sysArgs+3])                 #8
suba(1)                         #9
anda(0xfc)                      #10
st([vTmp])                      #11
ld([sysArgs+2])                 #12
adda([sysArgs+4])               #13
adda(1)                         #14
anda(0xfe)                      #15
ora([vTmp])                     #16
beq(pc()+3)                     #17
bra(pc()+3)                     #18
ld(0xff)                        #19
ld(0xfc)                        #19!
anda([channelMask])             #20
st([channelMask])               #21
ld([vCpuSelect])                #22
adda(1,Y)                       #23
jmp(Y,'NEXT')                   #24
ld(-26/2)                       #25

label('fsmST+#8')
st([fsmState])                  #8
ld([sysArgs+3],Y)               #9
ld([sysArgs+2],X)               #10
ld([vAC])                       #11
st([Y,X])                       #12
ld([sysArgs+2])                 #13
adda(1)                         #14
st([sysArgs+2])                 #15
ld([sysArgs+4])                 #16
suba(1)                         #17
st([sysArgs+4])                 #18
st([vAC])                       #19
ld([vCpuSelect])                #20
adda(1,Y)                       #21
jmp(Y,'NEXT')                   #22
ld(-24/2)                       #23


#-----------------------------------------------------------------------
#
#   $1600 ROM page 22: SYS_Exec FSM with compressed GT1 support
#
#-----------------------------------------------------------------------


fillers(until=0xff)
label('FSM16_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM16_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8

# Ensure labels defined here do not conflict
def fsmLab(n):
    return f'fsm16:{n}'

# Assemble u-opcode
def fsmAsm(op,arg=None):
    bra(fsmLab(op))
    ld(pc()+1) if arg is None else ld(arg)

# Usage fsmAsm('ST', arg)
# - [arg] := vACL
label(fsmLab('ST'))
ld(hi('fsmST#8'),Y)             #5
jmp(Y,'fsmST#8')                #6 + overlap

# Usage fsmAsm('LD', arg)
# - vACL = arg with arg=d or arg=[d]
label(fsmLab('LD'))
ld(hi('fsmOP#8'),Y)             #5
jmp(Y,'fsmOP#8')                #6 + overlap

# Usage fsmAsm('ADD', arg)
# - vACL += arg with arg=d or arg=[d]
label(fsmLab('ADD'))
ld(hi('fsmOP#8'),Y)             #5,7
jmp(Y,'fsmOP#8')                #6
adda([vAC])                     #7

# Usage fsmAsm('AND', arg)
# - vACL &= arg with arg=d or arg=[d]
label(fsmLab('AND'))
ld(hi('fsmOP#8'),Y)             #5,7
jmp(Y,'fsmOP#8')                #6
anda([vAC])                     #7

# Usage fsmAsm('LSR4')
# - right shift vACL by 4 positions (high nibble)
label(fsmLab('LSR4'))
ld(hi('fsmLSR4#8'),Y)           #5
jmp(Y,'fsmLSR4#8')              #6
st([fsmState])                  #7

# Usage fsmAsm('BNZ', arg)
# - branch if [vACL] is nonzero
label(fsmLab('BNZ'))
ld(hi('fsmBNZ#8'),Y)            #5,7
jmp(Y,'fsmBNZ#8')               #6
st([vTmp])                      #7

# Usage fsmAsm('BZ', arg)
# - branch if [vACL] is zero
label(fsmLab('BZ'))
ld(hi('fsmBZ#8'),Y)             #5
jmp(Y,'fsmBZ#8')                #6
st([vTmp])                      #7

# Usage fsmAsm('B', arg)
# - unconditional branch
# - can be the same as BL if sysArgs+6 can be trashed
label(fsmLab('B'))
#st([fsmState])                  #5
#bra('NEXT')                     #6
#ld(-8/2)                        #7

# Usage fsmAsm('BL', arg)
# - branch and link using sysArgs+6 as link register
# - call subroutine with fsmAsm('BL', 'label')
# - return from subroutine with fsmAsm('BL',[sysArgs+6])
label(fsmLab('BL'))
ld(hi('fsmBL#8'),Y)             #5
jmp(Y,'fsmBL#8')                #6
st([vTmp])                      #7

# Usage: fsmAsm('VRETNZ')
# - if vLR is nonzero, return to vCPU at address vLR.
label(fsmLab('VRETNZ'))
ld(hi('fsmVRETNZ#8'),Y)         #5
jmp(Y,'fsmVRETNZ#8')            #6
st([fsmState])                  #7

# Usage: fsmAsm('CHANMASK')
# - clear channelMask if segment [sysArgs[23],sysArgs[23]+sysArgs[4]]
#   overlaps OSCL/OSCH for audio channel 1-3
label(fsmLab('CHANMASK'))
ld(hi('fsmCHANMASK#8'),Y)       #5
jmp(Y,'fsmCHANMASK#8')          #6
st([fsmState])                  #7

# Usage: fsmAsm('ST+')
# - store vACL into [sysArgs23]
# - increment low address byte sysArgs2
# - decrements count sysArgs+4 and return it in vACL
label(fsmLab('ST+'))
ld(hi('fsmST+#8'),Y)            #5
jmp(Y,'fsmST+#8')               #6 + overlap

# Usage: fsmAsm('LUP')
# - copy rom byte at [sysArgs01] into vACL
# - increment [sysArgs01] skipping trampolines
label(fsmLab('LUP'))
st([fsmState])                  #5
ld([sysArgs+0])                 #6
suba(250)                       #7
beq(fsmLab('LUP#10'))           #8
ld([sysArgs+1],Y)               #9
adda(251)                       #10
st([sysArgs+0])                 #11
suba(1)                         #12
bra(fsmLab('LUP#15'))           #13
nop()                           #14
label(fsmLab('LUP#10'))
st([sysArgs+0])                 #10
ld([sysArgs+1])                 #11
adda(1)                         #12
st([sysArgs+1])                 #13
ld(250)                         #14
label(fsmLab('LUP#15'))
jmp(Y,251)                      #15
nop()                           #16

# Usage: fsmAsm('LDMATCH')
# - compute address sysArgs[23] minus offset sysFn[01] (no carry)
# - load byte at this address into vACL
label(fsmLab('LDMATCH'))
st([fsmState])                  #5,7
ld([sysArgs+3])                 #6
suba([sysFn+1],Y)               #7
ld([sysArgs+2])                 #8
suba([sysFn],X)                 #9
ld([Y,X])                       #10
st([vAC])                       #11
bra('NEXT')                     #12
ld(-14/2)                       #13

# Subroutine to copy [sysArgs+4] literals at [sysArgs+23]
label('se:copyLiteral')
fsmAsm('CHANMASK')
label('se:copyLiteral.1')
fsmAsm('LUP')
fsmAsm('ST+')
fsmAsm('BNZ', 'se:copyLiteral.1')
fsmAsm('BL', [sysArgs+6])

# Load uncompressed GT1
label('se:loadGt1:al')
fsmAsm('LUP')
fsmAsm('ST', sysArgs+2)
label('se:loadGt1:len')
fsmAsm('LUP')
fsmAsm('ST', sysArgs+4)
fsmAsm('BL', 'se:copyLiteral')
fsmAsm('LUP')
fsmAsm('ST', sysArgs+3)
fsmAsm('BNZ','se:loadGt1:al')

label('se:fin')
fsmAsm('LD', 'SYS_Exec_88')     # restore sysFn
fsmAsm('ST', sysFn)
fsmAsm('LD', hi('SYS_Exec_88'))
fsmAsm('ST', sysFn+1)
fsmAsm('VRETNZ')
fsmAsm('LUP')
fsmAsm('ST', vLR+1)
fsmAsm('LUP')
fsmAsm('ST', vLR)
label('se:ret')
fsmAsm('VRETNZ')
fsmAsm('B', 'se:ret')           # don't crash, loop.

# Entry point
# - Note that sysFn must be set to 0x0001 before this
label('se:exec')
fsmAsm('LUP')
fsmAsm('ST', sysArgs+3)
fsmAsm('BNZ', 'se:loadGt1:al')
fsmAsm('LUP')
fsmAsm('ST', sysArgs+2)
fsmAsm('ADD', 1)
fsmAsm('BNZ', 'se:loadGt1:len')
fsmAsm('LUP')                   # hi segment address
fsmAsm('B','se:loadGt1z')

# Load compressed GT1
label('se:loadGt1z:longseg')
fsmAsm('LUP')                   # hi segment address
fsmAsm('BZ', 'se:fin')
label('se:loadGt1z')
fsmAsm('ST', sysArgs+3)
fsmAsm('LUP')                   # lo segment address
fsmAsm('ST', sysArgs+2)
fsmAsm('ST', sysArgs+5)
label('se:loadGt1z:token')
fsmAsm('LUP')                   # read token
fsmAsm('ST', vAC+1)             # stash
fsmAsm('AND', 0x70)             # mask nLit
fsmAsm('BZ', 'se:loadGt1z:mcnt')
fsmAsm('LSR4')
fsmAsm('ST', sysArgs+4)
fsmAsm('ADD', 0xf9)             # is 7?
fsmAsm('BNZ', 'se:loadGt1z:lit')
fsmAsm('LUP')                   # extension byte for nlit
fsmAsm('ST', sysArgs+4)
label('se:loadGt1z:lit')
fsmAsm('BL', 'se:copyLiteral')
label('se:loadGt1z:mcnt')
fsmAsm('LD', [vAC+1])           # token
fsmAsm('AND', 0xf)
fsmAsm('BZ', 'se:loadGt1z:seg')
fsmAsm('ADD', 1)
fsmAsm('ST', sysArgs+4)
fsmAsm('ADD', 0xf0)             # is 16 (15+1)?
fsmAsm('BNZ', 'se:loadGt1z:offset')
fsmAsm('LUP')                   # extension byte for mcnt
fsmAsm('ST', sysArgs+4)
label('se:loadGt1z:offset')
fsmAsm('CHANMASK')
fsmAsm('LD', [vAC+1])           # token
fsmAsm('AND', 0x80)
fsmAsm('BZ', 'se:loadGt1z:match')
fsmAsm('LUP')                   # hi offset byte (or short offset)
fsmAsm('OFFSET')                # short offset magic
fsmAsm('LUP')                   # lo offset byte
fsmAsm('ST', sysFn)
label('se:loadGt1z:match')
fsmAsm('LDMATCH')
fsmAsm('ST+')
fsmAsm('BNZ', 'se:loadGt1z:match')
fsmAsm('B', 'se:loadGt1z:token')


label('se:loadGt1z:seg')
ld(fsmState, X)                 #3
st('se:loadGt1z:longseg', [X])  #4
ld([vAC+1])                     #5
bge('NEXT')                     #6
ld(-8/2)                        #7
ld([sysArgs+5])                 #8 short segment
st([sysArgs+2])                 #9
ld([sysArgs+3])                 #10
adda(1)                         #11
st([sysArgs+3])                 #12
st('se:loadGt1z:token', [X])    #13
bra('NEXT')                     #14
ld(-16/2)                       #15

label(fsmLab('OFFSET'))
st([fsmState])                  #5
ld([vAC])                       #6
st([sysFn+1])                   #7 save hi offset
bge('NEXT')                     #8 return for long offset
ld(-10/2)                       #9
ld('se:loadGt1z:match')         #10 short offset jumps here
st([fsmState])                  #11
ld([sysArgs+2])                 #12
suba([sysArgs+5])               #13 addr - segaddr
bpl(pc()+3)                     #14
bra(pc()+3)                     #15
ld(0xff)                        #16
ora(0x80)                       #16!
suba([vAC])                     #17 threshold - byte
ble('se:offset#20')             #18
ld(0)                           #19
st([sysFn+1])                   #20 offhi = 0
ld(0x81)                        #21
adda([vAC])                     #22
st([sysFn])                     #23 offlo = (byte+1) & 0x7f
bra('NEXT')                     #24
ld(-26/2)                       #25
label('se:offset#20')
ld(1)                           #20
st([sysFn+1])                   #21 offhi = 1
adda([vAC])                     #22
st([sysFn])                     #23 offlo = (byte + 1)
bra('NEXT')                     #24
ld(-26/2)                       #25


#-----------------------------------------------------------------------
#
#   $1700 ROM page 23: vCPU Prefix35 page
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

label('PREFIX35_PAGE')

def oplabel(name):
  define(name, 0x3500 | (pc() & 0xff))


# Instruction ADDL (35 00) [22+30+28 cycles]
# * Add long ([vAC]..[vAC]+3) to LAC
# * Trashes sysArgs[567]
# * No page crossings
oplabel('ADDL_v7')
bra('fsm1bop0#16')              #14
ld('addl#3a')                   #15

# Instruction COPYS (35 02 <vv> <d><nnnnnnn>)
# * This is front end for COPYN
# * <d>=0: copy <nnnnnnn> bytes from [vSP] to <vv>
#   <d>=1: copy <nnnnnnn> bytes from <vv> to [vSP]
oplabel('COPYS_v7')
bra('fsm18op2#16')              #14
ld('copys#3a')                  #15

# Instruction SUBL (35 04) [22+28+28 cycles]
# * Subtract long ([vAC]..[vAC]+3) from LAC
# * Trashes sysArgs[567]
# * No page crossings
oplabel('SUBL_v7')
bra('fsm1aop0#16')              #14
ld('subl#3a')                   #15

# Instruction ANDL (35 06) [22+28 cycles]
# * LAC := LAC & ([vAC]..[vAC]+3)
# * Trashes sysArgs[7]
oplabel('ANDL_v7')
bra('fsm1aop0#16')              #14
ld('andl#3a')                   #15

# instruction ORL (35 08) [22+28 cycles]
# * LAC := LAC | ([vAC]..[vAC]+3)
# * Trashes sysArgs[7]
oplabel('ORL_v7')
bra('fsm1aop0#16')              #14
ld('orl#3a')                    #15

# Instruction XORL (35 0a) [22+28 cycles]
# * LAC := LAC ^ ([vAC]..[vAC]+3)
# * Trashes sysArgs[7]
oplabel('XORL_v7')
bra('fsm1aop0#16')              #14
ld('xorl#3a')                   #15

# Instruction NEGVL (35 0c vv) [28+24 cycles]
# * Negate long (vv..vv+3)
# * Trashes sysArgs[67]
oplabel('NEGVL_v7')
bra('fsm1bop1#16')              #14
ld('negvl#3a')                  #15

# Instruction NEGX (35 0e) [22+14+24 cycles]
# * Negate extended accumulator LAX
# * Trashes sysArgs[67]
oplabel('NEGX_v7')
bra('fsm1bop0#16')              #14
ld('negx#3a')                   #15

# Instruction LSLVL (35 10 vv) [28+30 cycles]
# * Shift left long word (vv..vv+3)
# * No page crossings
# * Trashes sysArgs[67]
oplabel('LSLVL_v7')
bra('fsm1bop1#16')              #14
ld('lslvl#3a')                  #15

# Instruction LSLXA (35 12) [(n/8)*20+(38 to 282) total cycles]
# * Shift extended long accumulator LAX left by vACL positions
# * LAX := LAX << (vACL & 0x3f)
# * Trashes sysArgs[67]
oplabel('LSLXA_v7')
bra('fsm1eop0#16')              #14
ld('lslxa#3a')                  #15

# Instruction CMPLS (35 14) [22+20+24 max cycles]
# * Signed compare LAC with long ([vAC]..[vAC]+3)
# * On return sets vAC to a positive/negative/zero value
# * Trashes sysArgs[7]. No page crossings
oplabel('CMPLS_v7')
bra('fsm1eop0#16')              #14
ld('cmpls#3a')                  #15

# Instruction CMPLU (35 16) [22+20+24 max cycles]
# * Unsigned compare LAC with long ([vAC]..[vAC]+3)
# * On return sets vAC to a positive/negative/zero value
# * Trashes sysArgs[7]. No page crossings
oplabel('CMPLU_v7')
bra('fsm1eop0#16')              #14
ld('cmplu#3a')                  #15

# Instruction LSRXA (35 18) [20*(n/8)+(42,210,242,242,227,227,210,160)[n%8] cycles]
# * Shift extended long accumulator LAX right by vACL positions
# * LAX := LAX >> (vACL & 0x3f)
# * Trashes vAC, sysArgs[67]
oplabel('LSRXA_v7')
bra('fsm1cop0#16')              #14
ld('lsrxa#3a')                  #15

# Instruction RORX (35 1a) [total 198 cycles]
# * Rotate extended long accumulator LAX right
# * Trashes vAC, sysArgs[67]
#      ,-->--[LAX+4...LAX]-->--.
#      `--<------[VAC0]-----<--'
oplabel('RORX_v7')
bra('fsm1cop0#16')              #14
ld('rorx#3a')                   #15

# Instruction MACX (35 1c) [394 to 842 total cycles]
# * Add vACL (8 bits) times sysArgs[0..3] (32 bits) to LAX (40 bits)
# * LAC := LAX + sysArgs[3..0] * vACL.
# * Trashes sysArgs[4567].
oplabel('MACX_v7')
ld(hi('macx#17'),Y)             #14
jmp(Y,'macx#17')                #15

# Instruction LDLAC (35 1e), 36 cycles
# * Loads [vAC..vAC+3] into LAC
# * No page crossings
oplabel('LDLAC_v7')
ld(hi('ldlac#17'),Y)            #14
jmp(Y,'ldlac#17')               #15
# ld([vTicks])                  #16 [overlap]

# Instruction STLAC (35 20), 34 cycles
# * Store LAC into [vAC..vAC+3]
# * No page crossings
oplabel('STLAC_v7')
ld([vTicks])                    #14 overlap with ldlac
bra('stlac#17')                 #15 with shenanigans to preseve
ld(hi('stlac#19'),Y)            #16 STLAC location

# Instruction INCVL (35 23 xx), 22+(16/20/24/26) cycles
# * Increment long [xx..xx+3]
# * Trashes sysArgs[67]
oplabel('INCVL_v7')
bra('fsm1bop1#16')              #14
ld('incvl#3a')                  #15

# Instruction STFAC (35 25), 22+28 cycles (66 zero, 136 cross)
# * Store FAC into [vAC..vAC+4] in MFP format
# * Trashes T[0..3] sysArgs[0..7]
oplabel('STFAC_v7')
bra('fsm1eop0#16')              #14
ld('stfac#3a')                  #15

# Instruction LDFAC (35 27), 22+28+22 cycles (44 zero, 152 cross)
# * Load the MFP number [vAC..vAC+4] into FAC
# * Trashes T3, sysArgs[567]
oplabel('LDFAC_v7')
bra('fsm1aop0#16')              #14
ld('ldfac#3a')                  #15

# Instruction LDFARG (35 29), 22+28+22 cycles (44 zero, 152 cross)
# * This instruction is intended for the runtime.
#   Store the exponent of MFP number at [vAC..vAC+4] into v2L,
#   store its 40 bits extended mantissa in sysArgs[04],
#   sets bit 0 of vFAS to indicate if it sign differs from FAC's.
# * Trashes T3, sysArgs[567]
oplabel('LDFARG_v7')
bra('fsm1aop0#16')              #14
ld('ldfarg#3a')                 #15

# Instruction VSAVE (35 2b) 30+74 cycles
# * Save vCPU context at addresses XXe0-XXff where XX is vAC.
oplabel('VSAVE_v7')
ld(hi('vsave#17'),Y)            #14
jmp(Y,'vsave#17')               #15

# Instruction VRESTORE (35 2d)  28+58+30 cycles
# * Restore vCPU context saved at addresses XXe0-XXff where XX is vAC
#   branching to the saved pc. Also set frameCount:=frameCount|vACH.
oplabel('VRESTORE_v7')
ld(hi('vrestore#17'),Y)         #14
jmp(Y,'vrestore#17')            #15

### Instruction slot (35 2f) [formerly EXCH]
nop()                           #14
bra('reset')                    #15
nop()                           #16

# Instruction LEEKA (35 32 vv) 28+34 cycles
# * Copy long [vAC]...[vAC+3] to vv..vv+3
# * Trashes sysArgs[2-7]
oplabel('LEEKA_v7')
bra('fsm1bop1#16')              #14
ld('leeka#3a')                  #15

# Instruction LOKEA (35 34 vv) 28+34 cycles
# * Copy long vv..vv+3 to [vAC]...[vAC+3]
# * Trashes sysArgs[2-7]
oplabel('LOKEA_v7')
bra('fsm1bop1#16')              #14
ld('lokea#3a')                  #15

### Instruction slot (33 36)
nop()                           #14
bra('reset')                    #15
nop()                           #16

# Instruction RDIVS (35 39 xx) [~1250 cycles total]
# - Signed division of [xx] by vAC
# - Returns quotient in vAC and remainder in sysArgs[45]
# - Trashes sysArgs[0..7]
oplabel('RDIVS_v7')
bra('fsm14op1#16')              #14
ld('rdivs#3a')                  #15

# Instruction RDIVU (35 3b xx) [~1100 cycles total]
# - Unsigned division of [xx] by vAC
# - Returns quotient in vAC and remainder in sysArgs[45]
# - Trashes sysArgs[0..7]
oplabel('RDIVU_v7')
bra('fsm14op1#16')              #14
ld('rdivu#3a')                  #15

# Instruction MULW (35 3d xx) [434-546 cycles total]
# - Multiply vAC by var [xx]
# - Trashes sysArgs[0..7]
oplabel('MULW_v7')
bra('fsm14op1#16')              #14
ld('mulw#3a')                   #15

# Instruction BEQ (35 3f xx) [24 cycles]
# - Branch if zero (if(vACL==0)vPCL=xx)
assert (pc() & 255) == (symbol('EQ') & 255)
oplabel('BEQ')
ld([vAC+1])                     #14
label('beq#15')
ora([vAC])                      #15
beq('bccy#18')                  #16
label('bccn#17')
ld(1)                           #17
label('bccn#18*')
adda([vPC])                     #18
st([vPC])                       #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24//2)                      #22

# Instruction BLIT_v7 (35 48)
oplabel('BLIT_v7')
ld(hi('blit#17'),Y)             #14
jmp(Y,'blit#17')                #15

# Instruction FILL_v7 (35 4a) 
oplabel('FILL_v7')
ld(hi('fsm22op0#17'),Y)         #14
jmp(Y,'fsm22op0#17')            #15
ld('fill#3a')                   #16

# Instruction BGT (35 4d xx) [26 cycles]
# - Branch if positive (if(vACL>0)vPCL=xx)
assert (pc() & 255) == (symbol('GT') & 255)
oplabel('BGT')
ld([vAC+1])                     #14,19
bge('bgt#17')                   #15
blt('bccn#18')                  #16 AC!=0

# Instruction BLT (35 50 xx) [24 cycles]
# - Branch if negative (if(vACL<0)vPCL=xx)
assert (pc() & 255) == (symbol('LT') & 255)
oplabel('BLT')
ld([vAC+1])                     #14,17
bge('bccn#17')                  #15
blt('bccy#18')                  #16

# Instruction BGE (35 53 xx) [24 cycles]
# * Branch if positive or zero (if(vACL>=0)vPCL=xx)
assert (pc() & 255) == (symbol('GE') & 255)
oplabel('BGE')
ld([vAC+1])                     #14,17
blt('bccn#17')                  #15
bge('bccy#18')                  #16

# Instruction BLE (35 56 xx) [26/24 cycles]
# * Branch if negative or zero (if(vACL<=0)vPCL=xx)
assert (pc() & 255) == (symbol('LE') & 255)
oplabel('BLE')
ld([vAC+1])                     #14,17
blt('bccy#17')                  #15
ora([vAC])                      #16
beq('bccy*#19')                 #17
label('bccn#18')
ld([Y,X])                       #18
ld(1)                           #19
label('bccn*#20')
adda([vPC])                     #20
st([vPC])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26//2)                      #24

### Instruction slot (35 61)
bra('reset')                    #14
nop()                           #15

# Instruction DOKEI (35 63 ih il), 30 cycles
# * Store immediate word ihil at location [vAC]
oplabel('DOKEI_v7')
ld([Y,X])                       #14
st([Y,Xpp])                     #15
st([vTmp])                      #16 ih
ld([Y,X])                       #17 il
ld([vAC],X)                     #18
ld([vAC+1],Y)                   #19
st([Y,Xpp])                     #20
ld([vTmp])                      #21 ih
st([Y,X])                       #22
ld(2)                           #23
adda([vPC])                     #24
st([vPC])                       #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30//2)                      #28

# Instruction BNE (35 72 xx) [24 cycles]
# * Branch if not zero (if(vACL!=0)vPCL=xx)
assert (pc() & 255) == (symbol('NE') & 255)
oplabel('BNE')
ld([vAC+1])                     #14
ora([vAC])                      #15
beq('bccn#18*')                 #16
label('bccy#17')
ld(1)                           #17
label('bccy#18')
ld([Y,X])                       #18
label('bccy*#19')
st([vPC])                       #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24//2)                      #22

# stlac continuation (shenanigans)
label('stlac#17')
jmp(Y,'stlac#19')               #17
ld([vAC+1],Y)                   #18

# Instruction RESET_v7 [formerly ADDIV]
# * Causes a soft reset. Called by 'vReset' only.
oplabel('RESET_v7')
label('reset')
ld(hi('reset#17'),Y)            #14
jmp(Y,'reset#17')               #15

# bgt continuation
label('bgt#17')
ora([vAC])                      #17
beq('bccn*#20')                 #18
ld(1)                           #19
ld([Y,X])                       #20
st([vPC])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26//2)                      #24

# fsm relay (1 arg)
label('fsmxxop1#19')
st([vCpuSelect])                #19
ld([Y,X])                       #20
st([sysArgs+6])                 #21
ld(1)                           #22
adda([vCpuSelect],Y)            #23
adda([vPC])                     #24
st([vPC])                       #25
jmp(Y,'NEXT')                   #26
ld(-28/2)                       #27

# fsm14 relay (1 arg) for mulw, rdivu, rdivs
label('fsm14op1#16')
st([fsmState])                  #16
bra('fsmxxop1#19')              #17
ld(hi('FSM14_ENTER'))           #18

# fsm18 relay (1 arg) for copyn exbi
label('fsm18op1#16')
st([fsmState])                  #16
bra('fsmxxop1#19')              #17
ld(hi('FSM18_ENTER'))           #18

# fsm1b relay (1 arg) for incvl negvl lslvl
label('fsm1bop1#16')
st([fsmState])                  #16
bra('fsmxxop1#19')              #17
ld(hi('FSM1B_ENTER'))           #18

### Instruction slot (35 99) [or relay]
nop()
nop()
nop()

### Instruction slot (35 9c) [formetly SUBIV]
bra('reset')                    #14
nop()                           #15

### Free space for relay/instructions (31 bytes)

fillers(until=0xbd)

# fsm18 relay (2 args)
label('fsm18op2#16')
st([fsmState])                  #16
ld([Y,X])                       #17
st([Y,Xpp])                     #18
st([sysArgs+5])                 #19
ld([Y,X])                       #20
st([sysArgs+6])                 #21
ld(2)                           #22
adda([vPC])                     #23
st([vPC])                       #24
ld(hi('FSM18_ENTER'))           #25
st([vCpuSelect])                #26
adda(1,Y)                       #27
jmp(Y,'NEXT')                   #28
ld(-30/2)                       #29

# Instruction COPY (35 cb)
# * Copy up to vAC (max 256) bytes from [T3] to [T2]
# * Handles page crossings. Peak rate 10 bytes/scanline.
# * On return, T3 and T2 contain the next addresses
#   and vAC contains the number of bytes left to copy.
# * Origin: this is an improved version of the copy
#   opcode I wrote for ROMvX0.
oplabel('COPY_v7')
ld('copy#3a')                   #14
ld(hi('copy#18'),Y)             #15
jmp(Y,'copy#18')                #16
st([fsmState])                  #17

# Instruction COPYN (35 cf nn)
# * Copy nn bytes from [T3] to [T2].
# * Handles page crossings. Peak rate 10 bytes/scanline.
# * On return, T3 and T2 contain the next addresses.
# * N:Cycles 1:58 2:84 3:110 4:84 5:112 6:138 7:164 8:138
# * Origin: this is an improved version of the copy
#   opcode I wrote for ROMvX0.
oplabel('COPYN_v7')
bra('fsm18op1#16')              #14
ld('copy#3a')                   #15

# Instruction EXBA (35 d1 ii), 28+18 cycles
# * Byte at address [vAC] becomes ii.
# * Former value of bytes at address [vAC] ends up in vAC.
oplabel('EXBA_v7')
bra('fsm18op1#16')              #14
ld('exba#3a')                   #15

# Instruction NOTVL (35 d3 vv) [28+24 cycles]
# * Complements long (vv..vv+3)
# * Trashes sysArgs[67]
oplabel('NOTVL_v7')
bra('fsm1bop1#16')              #14
ld('notvl#3a')                  #15

# fsm1 relay (0 args)
label('fsm1aop0#16')
st([fsmState])                  #16
ld(hi('FSM1A_ENTER'))           #17
st([vCpuSelect])                #18
adda(1,Y)                       #19
jmp(Y,'NEXT')                   #20
ld(-22/2)                       #21

# Instruction MOVL (35 db yy xx), 30+30 cycles
# * Move four bytes long from [xx] to [yy]
# * No page crossings, trashes sysArgs,T0,T1
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2322#p2322
oplabel('MOVL_v7')
bra('fsm18op2#16')              #14
ld('movl#3a')                   #15

# Instruction MOVF (35 dd yy xx), 30+38 cycles
# * Move five bytes float from [xx] to [yy]
# * No page crossings, trashes sysArgs,T0,T1, but MOVF(xx,sysArgs0) works
# * Origin: https://forum.gigatron.io/viewtopic.php?p=2322#p2322
oplabel('MOVF_v7')
bra('fsm18op2#16')              #14
ld('movf#3a')                   #15

# fsm1b relay (0 args)
label('fsm1bop0#16')
st([fsmState])                  #16
ld(hi('FSM1B_ENTER'))           #17
st([vCpuSelect])                #18
adda(1,Y)                       #19
jmp(Y,'NEXT')                   #20
ld(-22/2)                       #21

# fsm1c relay (0 args)
label('fsm1cop0#16')
st([fsmState])                  #16
ld(hi('FSM1C_ENTER'))           #17
st([vCpuSelect])                #18
adda(1,Y)                       #19
jmp(Y,'NEXT')                   #20
ld(-22/2)                       #21

# fsm1e relay (0 arg)
label('fsm1eop0#16')
st([fsmState])                  #16
ld(hi('FSM1E_ENTER'))           #17
st([vCpuSelect])                #18
adda(1,Y)                       #19
jmp(Y,'NEXT')                   #20
ld(-22/2)                       #21

### Free space for relays/instructions (14 bytes)


#-----------------------------------------------------------------------
#
#   $1800 ROM page 24: FSM for copy instructions
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM18_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM18_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8



#----------------------------------------
# COPY COPYN

# COPY implementation
label('copy#18')
ld(hi('FSM18_ENTER'))           #18
st([vCpuSelect])                #19
ld([vAC])                       #20
st([sysArgs+6])                 #21
bne('copy#24')                  #22
ld([vAC+1])                     #23
bne('copy#26')                  #24
ld(hi('REENTER'),Y)             #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27
label('copy#24')
ld(0)                           #24
st([vAC])                       #25
bra('NEXT')                     #26
ld(-28/2)                       #27
label('copy#26')
suba(1)                         #26
st([vAC+1])                     #27
bra('NEXT')                     #28
ld(-30/2)                       #29


# COPY FSM
label('copy#3a')
ld([sysArgs+6])                 #3 State #a: entry point
anda(0xfc)                      #4
beq('copy#7a')                  #5 -> few bytes left
ld([vT3+1],Y)                   #6
ld([vT3],X)                     #7 try burst
ld([vT3])                       #8
adda(4)                         #9
st([vT3])                       #10
anda(0xfc)                      #11
beq('copy#14a')                 #12 -> page crossings
ld([Y,X])                       #13
st([Y,Xpp])                     #14
st([sysArgs+2])                 #15 read four
ld([Y,X])                       #16
st([Y,Xpp])                     #17
st([sysArgs+3])                 #18
ld([Y,X])                       #19
st([Y,Xpp])                     #20
st([sysArgs+4])                 #21
ld([Y,X])                       #22
st([sysArgs+5])                 #23
ld('copy#3d')                   #24 ->#d : store four
st([fsmState])                  #25
bra('NEXT')                     #26
ld(-28/2)                       #27
label('copy#14a')
ld([vT3])                       #14 undo vt3
suba(4)                         #15
st([vT3])                       #16
nop()                           #17
ld('copy#3b')                   #18 ->#b : copy1by1
st([fsmState])                  #19
bra('NEXT')                     #20
ld(-22/2)                       #21

label('copy#3b')
bra(pc()+1)                     #3 delay to sync with #a
nop()                           #4,5
ld([vT3+1],Y)                   #6
label('copy#7a')
ld([vT3],X)                     #7 copy one
ld([Y,X])                       #8 - used by both #a and #b
ld([vT2],X)                     #9 - loop until either sysArgs==0
ld([vT2+1],Y)                   #10  or a page is crossed.
st([Y,X])                       #11
ld(1)                           #12
adda([vT3])                     #13
st([vT3])                       #14
beq('copy#17b')                 #15
ld(1)                           #16
adda([vT2])                     #17
beq('copy#20b')                 #18
st([vT2])                       #19
ld([sysArgs+6])                 #20
suba(1)                         #21
beq('movl#24a')                 #22 ->exit (30 cycles)
st([sysArgs+6])                 #23
bra('NEXT')                     #24
ld(-26/2)                       #25 loop to #a or #b
label('copy#17b')
ld(1)                           #17 carry on vT3
adda([vT2])                     #18
st([vT2])                       #19
label('copy#20b')
ld('copy#3c')                   #20 carry on vT2
label('copy#21b')
st([fsmState])                  #21
bra('NEXT')                     #22 -> #c : resolve carries
ld(-24/2)                       #23

label('copy#3c')
ld([vT3])                       #3 resolve T2/T3 carries
beq('copy#6c1')                 #4 return to state #a or exit
bra(pc()+2)                     #5
label('copy#6c0')
ld(0)                           #6
adda([vT3+1])                   #7
st([vT3+1])                     #8
ld([vT2])                       #9
bne('copy#6c0')                 #10
bra(pc()+2)                     #11
label('copy#6c1')
ld(1)                           #12
adda([vT2+1])                   #13
st([vT2+1])                     #14
ld([sysArgs+6])                 #15
suba(1)                         #16
beq('copy#19c')                 #17
st([sysArgs+6])                 #18
bra('copy#21b')                 #19
ld('copy#3a')                   #20
label('copy#19c')
ld(hi('ENTER'))                 #19
st([vCpuSelect])                #20
adda(1,Y)                       #21
jmp(Y,'REENTER')                #22
ld(-26/2)                       #23

label('copy#3d')
ld([vT2],X)                     #3
ld([vT2+1],Y)                   #4
ld([vT2])                       #5
adda(4)                         #6
st([vT2])                       #7
anda(0xfc)                      #8
beq('copy#11d')                 #9 -> page crossings
ld([sysArgs+2])                 #10
st([Y,Xpp])                     #11
ld([sysArgs+3])                 #12
st([Y,Xpp])                     #13
ld([sysArgs+4])                 #14
st([Y,Xpp])                     #15
ld([sysArgs+5])                 #16
st([Y,Xpp])                     #17
ld([sysArgs+6])                 #18
suba(4)                         #19
beq('copy#22d')                 #20
st([sysArgs+6])                 #21
ld('copy#3a')                   #22
st([fsmState])                  #23
bra('NEXT')                     #24
ld(-26/2)                       #25
label('copy#22d')
ld(hi('ENTER'))                 #22
st([vCpuSelect])                #23
adda(1,Y)                       #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26
label('copy#11d')
st([Y,Xpp])                     #11 copy one only
ld([vT3])                       #12
suba(3)                         #13
st([vT3])                       #14 known noncarry
ld([vT2])                       #15
suba(3)                         #16
st([vT2])                       #17
beq('copy#20b')                 #18 maybe carry
ld([sysArgs+6])                 #19
suba(1)                         #20
st([sysArgs+6])                 #21 known nonzero
ld('copy#3b')                   #22 -> #b
st([fsmState])                  #23
bra('NEXT')                     #24
ld(-26/2)                       #25



# ----------------------------------------
# MOVL MOVF

# MOVL implementation
label('movl#3a')
ld(0,Y)                         #3
ld([sysArgs+6])                 #4
adda(1,X)                       #5
ld([Y,X])                       #6
st([Y,Xpp])                     #7
st([sysArgs+1])                 #8
ld([Y,X])                       #9
st([Y,Xpp])                     #10
st([sysArgs+2])                 #11
ld([Y,X])                       #12
st([sysArgs+3])                 #13
ld([sysArgs+6],X)               #14
ld([Y,X])                       #15
ld([sysArgs+5],X)               #16
st([Y,Xpp])                     #17
ld([sysArgs+1])                 #18
st([Y,Xpp])                     #19
ld([sysArgs+2])                 #20
st([Y,Xpp])                     #21
ld([sysArgs+3])                 #22
st([Y,Xpp])                     #23
label('movl#24a')
ld(hi('ENTER'))                 #24
st([vCpuSelect])                #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

# MOVF implementation
label('movf#3a')
ld([sysArgs+6])                 #3
adda(4,X)                       #4
ld([X])                         #5
st([vTmp])                      #6
ld([sysArgs+5])                 #7
adda(4,X)                       #8
ld([vTmp])                      #9
st([X])                         #10
ld('movl#3a')                   #11
st([fsmState])                  #12
nop()                           #13
bra('NEXT')                     #14
ld(-16/2)                       #15


# ----------------------------------------
# COPYS vv <d>nnnnnnn
# * d=0: copy from [vSP] to vv
#   d=1: copy from vv to [vSP]

label('copys#3a')
ld('copy#3a')                   #3
st([fsmState])                  #4
ld([sysArgs+6])                 #5
bmi('copys#8a')                 #6
anda(0x7f)                      #7
ld(0)                           #8
st([vT2+1],Y)                   #9
ld([sysArgs+5])                 #10
st([vT2])                       #11
bra('copys#14a')                #12
ld(vT3,X)                       #13
label('copys#8a')
st([sysArgs+6])                 #8
ld(0)                           #9
st([vT3+1],Y)                   #10
ld([sysArgs+5])                 #11
st([vT3])                       #12
ld(vT2,X)                       #13
label('copys#14a')
ld([vSP])                       #14
st([Y,Xpp])                     #15
ld([vSP+1])                     #16
st([Y,X])                       #17
bra('NEXT')                     #18
ld(-20/2)                       #19


# ----------------------------------------
# EXBA

label('exba#3a')
ld([vAC],X)                     #3
ld([vAC+1],Y)                   #4
ld([Y,X])                       #5
st([vAC])                       #6
ld(0)                           #7
st([vAC+1])                     #8
ld([sysArgs+6])                 #9
st([Y,X])                       #10
ld(hi('ENTER'))			#11
st([vCpuSelect])		#12
adda(1,Y)			#13
jmp(Y,'REENTER')		#14
ld(-18/2)			#15


#-----------------------------------------------------------------------
#
#   $1900 ROM page 25: vCPU ops
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)


# POKEA implementation
label('pokea#13')
ld(AC,X)                        #13
ld([X])                         #14
ld([vAC],X)                     #15
ld([vAC+1],Y)                   #16
st([Y,Xpp])                     #17
ld(hi('NEXTY'),Y)               #18
jmp(Y,'NEXTY')                  #19
ld(-22//2)                      #20

# DOKEA implementation (tentative)
label('dokea#13')
st([vTmp])                      #13
adda(1,X)                       #14
ld([X])                         #15 hi
ld([vTmp],X)                    #16
st([vTmp])                      #17 vTmp=hi
ld([X])                         #19 lo
ld([vAC],X)                     #19
ld([vAC+1],Y)                   #20
st([Y,Xpp])                     #21
ld([vTmp])                      #22
st([Y,X])                       #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28//2)                      #26

# DEEKA implementation
label('deeka#13')
st([sysArgs+7])                 #13
ld([vAC+1],Y)                   #14
ld([vAC])                       #15
adda(1,X)                       #16
ld([Y,X])                       #17 hi
st([vTmp])                      #18
ld([vAC],X)                     #19
ld([Y,X])                       #20 lo
ld([sysArgs+7],X)               #21
ld(0,Y)                         #22
st([Y,Xpp])                     #23
ld([vTmp])                      #24
st([Y,Xpp])                     #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30//2)                      #28

# POKEQ implementation
label('pokeq#13')
ld([vAC],X)                     #13
ld([vAC+1],Y)                   #14
st([Y,X])                       #15
ld(hi('NEXTY'),Y)               #16
jmp(Y,'NEXTY')                  #17
ld(-20//2)                      #18

# DOKEQ implementation
label('dokeq#13')
ld([vAC],X)                     #13
ld([vAC+1],Y)                   #14
st([Y,Xpp])                     #15
ld(0)                           #16
st([Y,X]);                      #18
ld(hi('NEXTY'),Y)               #19
jmp(Y,'NEXTY')                  #20
ld(-22//2)                      #21

# PEEKV implementation
label('peekv#13')
st([vTmp])                      #13
adda(1,X)                       #14
ld([X])                         #15
ld(AC,Y)                        #16
ld([vTmp],X)                    #17
ld([X])                         #18
ld(AC,X)                        #19
ld([Y,X])                       #20
st([vAC])                       #21
ld(0)                           #22
st([vAC+1])                     #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26

# DEEKV implementation
label('deekv#13')
adda(1,X)                       #13
ld([X])                         #14
ld(AC,Y)                        #15
ld([vTmp],X)                    #16
ld([X])                         #17
ld(AC,X)                        #18
ld([Y,X])                       #19
st([Y,Xpp])                     #20
st([vAC])                       #21
ld([Y,X])                       #22
st([vAC+1])                     #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26

# CMPWU implementation
label('cmpwu#13')
adda(1,X)                       #13
ld([vAC+1])                     #14 compare high bytes
xora([X])                       #15
beq('cmp#18')                   #16 equal -> check low byte
bgt('cmp#19')                   #17 same high bit -> subtract
ld([vAC+1])                     #18 otherwise:
xora(0x80)                      #19 vACH>=0x80>[X] if vACH[7]==1
ora(1)                          #20 vACH<0x80<=[X] if vACH[7]==0
label('cmp#21')
st([vAC+1])                     #21 return
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

label('cmp#19')
bra('cmp#21')                   #19 high bytes are different
suba([X])                       #20 but with same high bit

label('cmp#18')
ld([vTmp],X)                    #18 high bytes are equal.
label('cmpi#19')
ld([vAC])                       #19 same things with low bytes
xora([X])                       #20
bpl('cmp#23')                   #21
ld([vAC])                       #22
xora(0x80)                      #23
ora(1)                          #24
st([vAC+1])                     #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28
label('cmp#23')
suba([X])                       #23
st([vAC])                       #24
st([vAC+1])                     #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

# CMPWS implementation
label('cmpws#13')
adda(1,X)                       #13
ld([vAC+1])                     #14 compare high bytes
xora([X])                       #15
beq('cmp#18')                   #16 equal -> check low byte
bgt('cmp#19')                   #17 same high bit -> subtract
ld([vAC+1])                     #18 otherwise:
bra('cmp#21')                   #19 vACH>=0>[X] if vACH[7]==0
ora(1)                          #20 vACH<0<=[X] if vACH[7]==1

# CMPIU implementation
label('cmpiu#13')
st([vTmp])                      #13
ld([vAC+1])                     #14
bne('cmpiu#17')                 #15
ld(vTmp,X)                      #16
bra('cmpi#19')                  #17 vACH=0: reuse
label('cmpiu#17')
ld(1)                           #17 vACH!=0:
st([vAC+1])                     #18
ld(hi('REENTER'),Y)             #19
jmp(Y,'REENTER')                #20
ld(-24/2)                       #21

# CMPIS implementation
label('cmpis#13')
st([vTmp])                      #13
ld([vAC+1])                     #14
bne('cmpis#17')                 #15
ld(vTmp,X)                      #16
bra('cmpi#19')                  #17 vACH=0: reuse
label('cmpis#17')
ld(hi('REENTER'),Y)             #17 vACH!=0:
jmp(Y,'REENTER')                #18
ld(-22/2)                       #19

# MOVIW implementation
label('moviw#13')
ld([vPC+1],Y)                   #13
ld([vPC])                       #14
adda(2)                         #15
st([vPC],X)                     #16
ld([Y,X])                       #17
st([Y,Xpp])                     #18
st([vTmp])                      #19
ld([Y,X])                       #20
ld([sysArgs+7],X)               #21
ld(0,Y)                         #22
st([Y,Xpp])                     #23
ld([vTmp])                      #24
st([Y,X])                       #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

# ADDV immplementation
label('addv#13')
ld(0,Y)                         #13
ld(AC,X)                        #14
ld([Y,X])                       #15
adda([vAC])                     #16
st([Y,Xpp])                     #17
bmi('addv#20')                  #18
suba([vAC])                     #19
ora([vAC])                      #20
bmi('addv#23c')                 #21
ld([Y,X])                       #22
label('addv#23')
bra('addv#25')                  #23
adda([vAC+1])                   #24
label('addv#20')
anda([vAC])                     #20
bpl('addv#23')                  #21
ld([Y,X])                       #22
label('addv#23c')
adda([vAC+1])                   #23
adda(1)                         #24
label('addv#25')
st([Y,X])                       #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

# SUBV implementation
label('subv#13')
ld(0,Y)                         #13
ld(AC,X)                        #14
ld([Y,X])                       #15
bmi('subv#18')                  #16
suba([vAC])                     #17
st([Y,Xpp])                     #18
ora([vAC])                      #19
bmi('subv#22c')                 #20
ld([Y,X])                       #21
label('subv#22')
nop()                           #22
bra('addv#25')                  #23
suba([vAC+1])                   #24
label('subv#18')
st([Y,Xpp])                     #18
anda([vAC])                     #19
bpl('subv#22')                  #20
ld([Y,X])                       #21
label('subv#22c')
suba([vAC+1])                   #22
bra('addv#25')                  #23
suba(1)                         #24

# JNE implementation (24/26)
# - always slower than BNE (24/24)
label('jne#13')
ld([vAC+1])                     #13
ora([vAC])                      #14
label('jne#15')
beq('jccn#17')                  #15
label('jccy#16')                # branch in 26 cycles
ld([vPC+1],Y)                   #16
label('jccy*#17')               # branch in 26 cycles (with Y=PCH)
ld([Y,X])                       #17
st([Y,Xpp])                     #18
st([vPC])                       #19
ld([Y,X])                       #20
st([vPC+1])                     #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# JEQ implementation (24/26)
# - always slower than BEQ (24/24)
label('jeq#13')
ld([vAC+1])                     #13
ora([vAC])                      #14
label('jeq#15')
beq('jccy*#17')                 #15
ld([vPC+1],Y)                   #16
label('jccn#17')                # pass in 24 cycles
ld(1)                           #17
label('jccn*#18')               # pass in 24 cycles (with AC=1)
adda([vPC])                     #18
st([vPC])                       #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

# JGT implementation (22-24/26) [with vACH in AC]
# - always faster than BGT (26/26)
label('jgt#13')
bpl('jne#15')                   #13
ora([vAC])                      #14
label('jccn#15')
ld(1)                           #15
adda([vPC])                     #16
st([vPC])                       #17
ld(hi('NEXTY'),Y)               #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20

# JGE implementation (22/24) [with vACH in AC]
# - always faster than BGE (24/24)
label('jge#13')
bmi('jccn#15')                  #13
label('jccy#15')                # branch in 24 cycles
ld([vPC+1],Y)                   #14
label('jccy*#15')               # branch in 24 cycles (with Y=PCH)
ld([Y,X])                       #15
st([Y,Xpp])                     #16
st([vPC])                       #17
ld([Y,X])                       #18
st([vPC+1])                     #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

# JLT implementation (22/24) [with vACH in AC]
# - always faster than BLT (24/24)
label('jlt#13')
bmi('jccy*#15')                 #13
ld([vPC+1],Y)                   #14
ld(1)                           #15
adda([vPC])                     #16
st([vPC])                       #17
ld(hi('NEXTY'),Y)               #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20

# JLE implementation (22-24/26) [with vACH in AC]
# - faster than BLE (26/24) when passing, slower when branching
label('jle#13')
bpl('jeq#15')                   #13
ora([vAC])                      #14
bra('jccy*#17')                 #15
ld([vPC+1],Y)                   #16



#-----------------------------------------------------------------------
#
#   $1A00 ROM page 28: FSM for vCPU long ops
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM1A_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM1A_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8

# ----------------------------------------
# SUBL implementation

label('subl#3a')
ld('subl#3b')                   #3
st([fsmState])                  #4
ld([vAC+1],Y)                   #5
ld([vAC],X)                     #6
ld([vLAC])                      #7  b0
bmi('subl#10aa')                #8
suba([Y,X])                     #9
st([vLAC])                      #10
ora([Y,X])                      #11
bmi('subl#14aa')                #12
ld([vAC])                       #13
label('subl#14a')
adda(1,X)                       #14
bra('subl#17aa')                #15
ld([Y,X])                       #16

label('subl#10aa')
st([vLAC])                      #10
anda([Y,X])                     #11
bpl('subl#14a')                 #12
ld([vAC])                       #13
label('subl#14aa')
adda(1,X)                       #14
ld([Y,X])                       #15
adda(1)                         #16
label('subl#17aa')
st([vTmp])                      #17
ld([vLAC+1])                    #18 b1
bmi('subl#21aaa')               #19
suba([vTmp])                    #20
st([vLAC+1])                    #21
ora([Y,X])                      #22
anda(0x80,X)                    #23
ld([X])                         #24
st([sysArgs+6])                 #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('subl#21aaa')
st([vLAC+1])                    #21
anda([Y,X])                     #22
anda(0x80,X)                    #23
ld([X])                         #24
st([sysArgs+6])                 #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('subl#3b')
ld([vAC+1],Y)                   #3
ld([vAC])                       #4 b2
adda(2,X)                       #5
ld([vLAC+2])                    #6
bmi(pc()+6)                     #7
suba([Y,X])                     #8
suba([sysArgs+6])               #9
st([vLAC+2])                    #10
bra(pc()+6)                     #11
ora([Y,X])                      #12
suba([sysArgs+6])               #9
st([vLAC+2])                    #10
nop()                           #11
anda([Y,X])                     #12
anda(0x80,X)                    #13
ld([X])                         #14
st([sysArgs+6])                 #15
ld([vAC])                       #16 b2
adda(3,X)                       #17
ld([vLAC+3])                    #18 b3
suba([Y,X])                     #19
suba([sysArgs+6])               #20
st([vLAC+3])                    #21
label('fsm1anexty#22')
ld(hi('ENTER'))                 #22
st([vCpuSelect])                #23
adda(1,Y)                       #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26

# ----------------------------------------
# long bitwise ops: ANDL ORL XORL

label('andl#3a')
ld([vAC+1],Y)                   #3
ld([vAC],X)                     #4
ld([Y,X])                       #5
st([Y,Xpp])                     #6
anda([vLAC])                    #7
st([vLAC])                      #8
ld([Y,X])                       #9
st([Y,Xpp])                     #10
anda([vLAC+1])                  #11
st([vLAC+1])                    #12
ld([Y,X])                       #13
st([Y,Xpp])                     #14
anda([vLAC+2])                  #15
st([vLAC+2])                    #16
ld([Y,X])                       #17
anda([vLAC+3])                  #18
nop()                           #19
label('andl#20a')
bra('fsm1anexty#22')            #20
st([vLAC+3])                    #21

label('orl#3a')
ld([vAC+1],Y)                   #3,21
ld([vAC],X)                     #4
ld([Y,X])                       #5
st([Y,Xpp])                     #6
ora([vLAC])                     #7
st([vLAC])                      #8
ld([Y,X])                       #9
st([Y,Xpp])                     #10
ora([vLAC+1])                   #11
st([vLAC+1])                    #12
ld([Y,X])                       #13
st([Y,Xpp])                     #14
ora([vLAC+2])                   #15
st([vLAC+2])                    #16
ld([Y,X])                       #17
bra('andl#20a')                 #18
ora([vLAC+3])                   #19

label('xorl#3a')
ld([vAC+1],Y)                   #3,21
ld([vAC],X)                     #4
ld([Y,X])                       #5
st([Y,Xpp])                     #6
xora([vLAC])                    #7
st([vLAC])                      #8
ld([Y,X])                       #9
st([Y,Xpp])                     #10
xora([vLAC+1])                  #11
st([vLAC+1])                    #12
ld([Y,X])                       #13
st([Y,Xpp])                     #14
xora([vLAC+2])                  #15
st([vLAC+2])                    #16
ld([Y,X])                       #17
bra('andl#20a')                 #18
xora([vLAC+3])                  #19


# ----------------------------------------
# LDFAC LDFARG

# LDFAC implementation
label('ldfac#3a')
ld([vAC],X)                     #3
ld([vAC+1],Y)                   #4
ld([Y,X])                       #5
beq('ldfac#8a')                 #6
st([vFAE])                      #7 exponent
ld([vAC])                       #8
adda(1,X)                       #9
anda(0xfc)                      #10
xora(0xfc)                      #11
beq('ldfac#14a')                #12
ld('ldfac#3c')                  #13
st([fsmState])                  #14
ld([Y,X])                       #15 no crossings
st([Y,Xpp])                     #16
st([vLAX+4])                    #17
ld([Y,X])                       #18
st([Y,Xpp])                     #19
st([vLAX+3])                    #20
ld([Y,X])                       #21
st([Y,Xpp])                     #22
st([vLAX+2])                    #23
ld([Y,X])                       #24
st([vLAX+1])                    #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('ldfac#8a')
nop()                           #8
ld(vLAX,X)                      #9
label('ldfacrg#10a')
ld(0,Y)                         #10
st([Y,Xpp])                     #11
st([Y,Xpp])                     #12
st([Y,Xpp])                     #13
st([Y,Xpp])                     #14
st([Y,X])                       #15
label('ldfacrg#16')
ld(hi('ENTER'))                 #16
st([vCpuSelect])                #17
adda(1,Y)                       #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20

label('ldfac#14a')
st([sysArgs+6])                 #14 page crossings
nop()                           #15
ld(vLAX)                        #16
label('ldfacrg#17a')
st([vT3+1])                     #17
adda(4)                         #18
st([vT3])                       #19
ld('ldfacrg#3b')                #20 to slow copy
st([fsmState])                  #21
bra('NEXT')                     #22
ld(-24/2)                       #23

label('ldfacrg#3b')
ld(1)                           #3
adda([vAC])                     #4
st([vAC],X)                     #5
beq('ldfacrg#3b')               #6
bra(pc()+2)                     #7
ld(0)                           #8
adda([vAC+1])                   #9
st([vAC+1],Y)                   #10
ld([Y,X])                       #11
ld([vT3],X)                     #12
st([X])                         #13
ld([vT3])                       #14
suba(1)                         #15
st([vT3])                       #16
xora([vT3+1])                   #17
bne('NEXT')                     #18
ld(-20/2)                       #19
ld([sysArgs+6])                 #20
st([fsmState])                  #21
bra('NEXT')                     #22
ld(-24/2)                       #23

label('ldfac#3c')
ld(0)                           #3
st([vLAX])                      #4 mantissa extension
ld([vLAX+4])                    #5
xora([vFAS])                    #6 sign
anda(0x80)                      #7
ld(AC,X)                        #8
ora([X])                        #9
xora([vFAS])                    #10
st([vFAS])                      #11
ld([vLAX+4])                    #12 high byte
ora(0x80)                       #13
bra('ldfacrg#16')               #14
st([vLAX+4])                    #16

# LDFARG implementation
label('ldfarg#3a')
ld([vAC],X)                     #3
ld([vAC+1],Y)                   #4
ld([Y,X])                       #5
beq('ldfarg#8a')                #6
st([vT2])                       #7
ld([vAC])                       #8
adda(1,X)                       #9
anda(0xfc)                      #10
xora(0xfc)                      #11
beq('ldfarg#14a')               #12
ld('ldfarg#3c')                 #13
st([fsmState])                  #14
ld([Y,X])                       #15
st([Y,Xpp])                     #16
st([sysArgs+4])                 #17
ld([Y,X])                       #18
st([Y,Xpp])                     #19
st([sysArgs+3])                 #20
ld([Y,X])                       #21
st([Y,Xpp])                     #22
st([sysArgs+2])                 #23
ld([Y,X])                       #24
st([sysArgs+1])                 #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('ldfarg#8a')
bra('ldfacrg#10a')              #8
ld(sysArgs+0,X)                 #9

label('ldfarg#14a')
st([sysArgs+6])                 #14 page crossings
bra('ldfacrg#17a')              #15
ld(sysArgs+0)                   #16

label('ldfarg#3c')
ld(0)                           #3
st([sysArgs+0])                 #4 mantissa extension
ld([sysArgs+4])                 #5
xora([vFAS])                    #6 sign
anda(0x80,X)                    #7
ld([vFAS])                      #8
anda(0xfe)                      #9
ora([X])                        #10
st([vFAS])                      #11
ld([sysArgs+4])                 #12 high byte
ora(0x80)                       #13
bra('ldfacrg#16')               #14
st([sysArgs+4])                 #15



#-----------------------------------------------------------------------
#
#   $1b00 ROM page 29:  FSM for vCPU long ops
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM1B_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM1B_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8

# ----------------------------------------
# ADDL implementation

label('addl#3a')
ld('addl#3b')                   #3
st([fsmState])                  #4
ld([vAC+1],Y)                   #5
ld([vAC],X)                     #6
nop()                           #7
ld([Y,X])                       #8
adda([vLAC])                    #9
st([vLAC])                      #10 b0
bmi('addl#13aa')                #11
suba([Y,X])                     #12
label('addl#13a')
ora([Y,X])                      #13
bmi('addl#16aa')                #14
ld([vAC])                       #15
label('addl#16a')
adda(1,X)                       #16
bra('addl#19aa')                #17
ld([Y,X])                       #18

label('addl#13aa')
anda([Y,X])                     #13
bpl('addl#16a')                 #14
ld([vAC])                       #15
label('addl#16aa')
adda(1,X)                       #16
ld([Y,X])                       #17
adda(1)                         #18
label('addl#19aa')
st([vTmp])                      #19
adda([vLAC+1])                  #20
st([vLAC+1])                    #21 b1
bmi('addl#24aaa')               #22
suba([vTmp])                    #23
ora([Y,X])                      #24
anda(0x80,X)                    #25
ld([X])                         #26
st([sysArgs+6])                 #27
bra('NEXT')                     #28
ld(-30/2)                       #29

label('addl#24aaa')
anda([Y,X])                     #24
anda(0x80,X)                    #25
ld([X])                         #26
st([sysArgs+6])                 #27
bra('NEXT')                     #28
ld(-30/2)                       #29

label('addl#3b')
ld([vAC+1],Y)                   #3
ld([vAC])                       #4
adda(2,X)                       #5
ld([Y,X])                       #6
adda([sysArgs+6])               #7
st([vTmp])                      #8
adda([vLAC+2])                  #9
st([vLAC+2])                    #10 b2
bmi('addl#13bb')                #11
suba([vTmp])                    #12
ora([Y,X])                      #13
bmi('addl#16bb')                #14
ld([vAC])                       #15
label('addl#16b')
adda(3,X)                       #16
bra('addl#19bb')                #17
ld([Y,X])                       #18

label('addl#13bb')
anda([Y,X])                     #13
bpl('addl#16b')                 #14
ld([vAC])                       #15
label('addl#16bb')
adda(3,X)                       #16
ld([Y,X])                       #17
adda(1)                         #18
label('addl#19bb')
adda([vLAC+3])                  #19
st([vLAC+3])                    #20 b3
ld(hi('ENTER'))                 #21
st([vCpuSelect])                #22
adda(1,Y)                       #23
jmp(Y,'REENTER')                #24
ld(-28/2)                       #25

# ----------------------------------------
# NEGX NEGVL

label('negx#3a')
ld(vLAC)                        #3
st([sysArgs+6])                 #4
ld(0)                           #5
suba([vLAC-1])                  #6
st([vLAC-1])                    #7
beq(pc()+3)                     #8
bra(pc()+3)                     #9
ld('notvl#3a')                  #10
ld('negvl#3a')                  #10
st([fsmState])                  #11
bra('NEXT')                     #12

label('notvl#3a')
ld(-14/2)                       #13,3
ld(0,Y)                         #4
ld([sysArgs+6],X)               #5
ld(0xff)                        #6
xora([Y,X])                     #7
st([Y,Xpp])                     #8
label('notvl#9a')
ld(0xff)                        #9
xora([Y,X])                     #10
st([Y,Xpp])                     #11
label('notvl#12a')
ld(0xff)                        #12
xora([Y,X])                     #13
st([Y,Xpp])                     #14
label('notvl#15a')
ld(0xff)                        #15
xora([Y,X])                     #16
label('notvl#17a')
st([Y,X])                       #17
ld(hi('ENTER'))                 #18
st([vCpuSelect])                #19
adda(1,Y)                       #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

label('negvl#3a')
ld(0,Y)                         #3
ld([sysArgs+6],X)               #4
ld(0)                           #5
suba([Y,X])                     #6
bne('notvl#9a')                 #7
st([Y,Xpp])                     #8
suba([Y,X])                     #9
bne('notvl#12a')                #10
st([Y,Xpp])                     #11
suba([Y,X])                     #12
bne('notvl#15a')                #13
st([Y,Xpp])                     #14
bra('notvl#17a')                #15
suba([Y,X])                     #16



# ----------------------------------------
# LSLVL

label('lslvl#3a')
ld(0,Y)                         #3
ld([sysArgs+6],X)               #4
ld([Y,X])                       #5  b0
blt('lslvl#8aa' )               #6
adda([Y,X])                     #7
st([Y,Xpp])                     #8
ld([Y,X])                       #9  b1
nop()                           #10
blt('lslvl#13aa')               #11
label('lslvl#12a')
adda([Y,X])                     #12
st([Y,Xpp])                     #13
ld([Y,X])                       #14  b2
nop()                           #15
blt('lslvl#18aa')               #16
label('lslvl#17a')
adda([Y,X])                     #17
st([Y,Xpp])                     #18
ld([Y,X])                       #19  b3
bra('lslvl#22aa')               #20
adda([Y,X])                     #21

label('lslvl#8aa')
st([Y,Xpp])                     #8
ld([Y,X])                       #9 b1
bpl('lslvl#12a')                #10
adda(1)                         #11
adda([Y,X])                     #12
label('lslvl#13aa')
st([Y,Xpp])                     #13
ld([Y,X])                       #14 b2
bpl('lslvl#17a')                #15
adda(1)                         #16
adda([Y,X])                     #17
label('lslvl#18aa')
st([Y,Xpp])                     #18
ld([Y,X])                       #19 b3
adda(1)                         #20
adda([Y,X])                     #21
label('lslvl#22aa')
st([Y,X])                       #22
ld(hi('ENTER'))                 #23
st([vCpuSelect])                #24
adda(1,Y)                       #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27


# ----------------------------------------
# INCVL

label('incvl#3a')
ld(hi('ENTER'))                 #3
st([vCpuSelect])                #4
ld([sysArgs+6],X)               #5
ld(0,Y)                         #6
ld(1)                           #7
adda([Y,X])                     #8
st([Y,Xpp])                     #9
bne('incvl#12')                 #10
ld(1)                           #11
adda([Y,X])                     #12
st([Y,Xpp])                     #13
bne('incvl#16')                 #14
ld(1)                           #15
adda([Y,X])                     #16
st([Y,Xpp])                     #17
bne('incvl#20')                 #18
ld(1)                           #19
adda([Y,X])                     #20
st([Y,X])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24
label('incvl#20')
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22
label('incvl#16')
ld(hi('NEXTY'),Y)               #16
jmp(Y,'NEXTY')                  #17
ld(-20/2)                       #18
label('incvl#12')
ld(hi('NEXTY'),Y)               #12
jmp(Y,'NEXTY')                  #13
ld(-16/2)                       #14



# ----------------------------------------
# LEEKA/LOKEA

label('retry1b#6')
bra('NEXT')                     #6
ld(-8/2)                        #7

label('leeka#3a')
adda(min(0,maxTicks-34/2))      #3
blt('retry1b#6')                #4
ld([vAC],X)                     #5
ld([vAC+1],Y)                   #6
ld([Y,X])                       #7
st([Y,Xpp])                     #8
st([sysArgs+2])                 #9
ld([Y,X])                       #10
st([Y,Xpp])                     #11
st([sysArgs+3])                 #12
ld([Y,X])                       #13
st([Y,Xpp])                     #14
st([sysArgs+4])                 #15
ld([Y,X])                       #16
st([sysArgs+5])                 #17
ld(0,Y)                         #18
ld([sysArgs+6],X)               #19
ld([sysArgs+2])                 #20
st([Y,Xpp])                     #21
ld([sysArgs+3])                 #22
st([Y,Xpp])                     #23
ld([sysArgs+4])                 #24
st([Y,Xpp])                     #25
ld([sysArgs+5])                 #26
st([Y,Xpp])                     #27
ld(hi('ENTER'))                 #28
st([vCpuSelect])                #29
adda(1,Y)                       #30
jmp(Y,'NEXTY')                  #31
ld(-34/2)                       #32

label('lokea#3a')
adda(min(0,maxTicks-34/2))      #3
blt('retry1b#6')                #4
ld(0,Y)                         #5
ld([sysArgs+6],X)               #6
ld([Y,X])                       #7
st([Y,Xpp])                     #8
st([sysArgs+2])                 #9
ld([Y,X])                       #10
st([Y,Xpp])                     #11
st([sysArgs+3])                 #12
ld([Y,X])                       #13
st([Y,Xpp])                     #14
st([sysArgs+4])                 #15
ld([Y,X])                       #16
st([sysArgs+5])                 #17
ld([vAC],X)                     #18
ld([vAC+1],Y)                   #19
ld([sysArgs+2])                 #20
st([Y,Xpp])                     #21
ld([sysArgs+3])                 #22
st([Y,Xpp])                     #23
ld([sysArgs+4])                 #24
st([Y,Xpp])                     #25
ld([sysArgs+5])                 #26
st([Y,Xpp])                     #27
ld(hi('ENTER'))                 #28
st([vCpuSelect])                #29
adda(1,Y)                       #30
jmp(Y,'NEXTY')                  #31
ld(-34/2)                       #32




#-----------------------------------------------------------------------
#
#   $1C00 ROM page 28: FSM for long right shift ops
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM1C_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM1C_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8


# ----------------------------------------
# LSRXA

label('lsrxa#3a')
ld([vAC])                       #3
anda(0x3f)                      #4
suba(8)                         #5
blt('lsrxa#8a')                 #6
st([vAC])                       #7
ld([vLAX+1])                    #8
st([vLAX+0])                    #9
ld([vLAX+2])                    #10
st([vLAX+1])                    #11
ld([vLAX+3])                    #12
st([vLAX+2])                    #13
ld([vLAX+4])                    #14
st([vLAX+3])                    #15
ld(0)                           #16
st([vLAX+4])                    #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('lsrxa#8a')
anda(7)                         #8
adda(AC)                        #9
adda('lsrax#13')                #10
bra(AC)                         #11
nop()                           #12

label('lsrax#13')
bra('lsraxq#15')                #13 <<0
ld(hi('ENTER'))                 #14
bra('lsraxs#15')                #13 <<1
ld('rorx1#3')                   #14
bra('lsraxn#15')                #13 <<2
ld('rorx2#13')                   #14
bra('lsraxn#15')                #13 <<3
ld('rorx3#13')                  #14
bra('lsraxn#15')                #13 <<4
ld('rorx4#13')                  #14
bra('lsraxn#15')                #13 <<5
ld('rorx5#13')                  #14
bra('lsraxs#15')                #13 <<6
ld('rorx6#3')                   #14
bra('lsraxs#15')                #13 <<7
ld('rorx7#3')                   #14

label('lsraxq#15')
st([vCpuSelect])                #15
adda(1,Y)                       #16
jmp(Y,'NEXTY')                  #17
ld(-20/2)                       #18

label('lsraxs#15')
st([fsmState])                  #15
ld(vLAX+5)                      #16
st([sysArgs+6])                 #17
ld(0)                           #18
st([vAC])                       #19
bra('NEXT')                     #20
ld(-22/2)                       #21

label('lsraxn#15')
st([sysArgs+5])                 #15
ld('rorxn#3')                   #16
st([fsmState])                  #17
ld(vLAX+5)                      #18
st([sysArgs+6])                 #19
ld(0)                           #20
st([vAC])                       #21
bra('NEXT')                     #22
ld(-24/2)                       #23

# ----------------------------------------
# RORX

label('rorx#3a')
ld('rorx1#3')                   #3
st([fsmState])                  #4
ld(vLAX+5)                      #5
st([sysArgs+6])                 #6
nop()                           #7
bra('NEXT')                     #8
ld(-10/2)                       #9


# ----------------------------------------
# Right shift workers

label('rorx#9')
ld(hi('ENTER'))                 #9
st([vCpuSelect])                #10
adda(1,Y)                       #11
jmp(Y,'REENTER')                #12
ld(-16/2)                       #13

label('rorx1#3')
ld([sysArgs+6])                 #3
suba(1)                         #4
st([sysArgs+6],X)               #5
suba(vLAX)                      #6
blt('rorx#9')                   #7
ld([vAC])                       #8
anda(1)                         #9
adda(127)                       #10
anda(128)                       #11
st([vAC+1])                     #12
ld('rorx#25')                   #13
st([vTmp])                      #14
ld([X])                         #15
st([vAC])                       #16
bra('rorx1#19')                 #17
anda(0b11111110)                #19

label('rorxn#3')
adda(min(0,maxTicks-36/2))      #3 >>2 state
blt('rorxn#6')                  #4
ld([sysArgs+6])                 #5
suba(vLAX)                      #6
ble('rorx#9')                   #7
adda(vLAX-1)                    #8
st([sysArgs+6],X)               #9
ld([vAC])                       #10
bra([sysArgs+5])                #11
adda(AC)                        #12
label('rorxn#6')
bra('NEXT')                     #6 restart
ld(-8/2)                        #7

label('rorx2#13')
adda(AC)                        #13
adda(AC)                        #14
adda(AC)                        #15
adda(AC)                        #16
adda(AC)                        #17
st([vAC+1])                     #18
ld('rorx#31')                   #19
st([vTmp])                      #20
ld([X])                         #21
st([vAC])                       #22
anda(0b11111100)                #23
ora (0b00000001)                #24
label('rorx1#19')
label('rorx2#25')
ld(hi('shiftTable'),Y)          #19,25
jmp(Y,AC)                       #20,26
bra(255)                        #21,27

label('rorx3#13')
adda(AC)                        #13
adda(AC)                        #14
adda(AC)                        #15
adda(AC)                        #16
st([vAC+1])                     #17
ld('rorx#31')                   #18
st([vTmp])                      #19
ld([X])                         #20
st([vAC])                       #21
anda(0b11111000)                #22
bra('rorx2#25')                 #23
ora (0b00000011)                #24

label('rorx4#13')
adda(AC)                        #13
adda(AC)                        #14
adda(AC)                        #15
st([vAC+1])                     #16
ld('rorx#29')                   #17
st([vTmp])                      #18
ld([X])                         #19
st([vAC])                       #20
anda(0b11110000)                #21
ora (0b00000111)                #22
label('rorx4#23')
ld(hi('shiftTable'),Y)          #23
jmp(Y,AC)                       #24
bra(255)                        #25

label('rorx5#13')
adda(AC)                        #13
adda(AC)                        #14
st([vAC+1])                     #15
ld('rorx#29')                   #16
st([vTmp])                      #17
ld([X])                         #18
st([vAC])                       #19
anda(0b11100000)                #20
bra('rorx4#23')                 #21
ora (0b00001111)                #22

label('rorx6#3')
ld([sysArgs+6])                 #3
suba(1)                         #4
st([sysArgs+6],X)               #5
suba(vLAX)                      #6
blt('rorx#9')                   #7
ld([vAC])                       #8
adda(AC)                        #9
adda(AC)                        #10
st([vAC+1])                     #11
ld('rorx#25')                   #12
st([vTmp])                      #13
ld([X])                         #14
st([vAC])                       #15
anda(0b11000000)                #16
bra('rorx1#19')                 #17
ora (0b00011111)                #18

label('rorx7#3')
ld([sysArgs+6])                 #3
suba(1)                         #4
st([sysArgs+6],X)               #5
suba(vLAX)                      #6
blt('rorx#9')                   #7
ld([vAC])                       #8
adda(AC)                        #9
st([vAC+1])                     #10
ld([X])                         #11
st([vAC])                       #12
anda(0x80,X)                    #13
ld([X])                         #14
ora([vAC+1])                    #15
ld([sysArgs+6],X)               #16
st([X])                         #17
bra('NEXT')                     #18
ld(-20/2)                       #19


#----------------------------------------
# STXW LDXW

label('ldxw#3a')
ld([vPC+1],Y)                   #3
ld([vPC])                       #4
adda(2)                         #5
st([vPC],X)                     #6
ld([Y,X])                       #7
st([Y,Xpp])                     #8
adda([sysArgs+5])               #9
st([vTmp])                      #10
bmi('ldxw#13a')                 #11
suba([sysArgs+5])               #12
ora([sysArgs+5])                #13
bmi('ldxw#16a')                 #14
ld([Y,X])                       #15
bra('ldxw#18a')                 #16
adda([sysArgs+6],Y)             #17
label('ldxw#13a')
anda([sysArgs+5])               #13
bmi('ldxw#16a')                 #14
ld([Y,X])                       #15
bra('ldxw#18a')                 #16
adda([sysArgs+6],Y)             #17
label('ldxw#16a')
adda(1)                         #16
adda([sysArgs+6],Y)             #17
label('ldxw#18a')
ld([vTmp],X)                    #18
ld([Y,X])                       #19
st([Y,Xpp])                     #20
st([vAC])                       #21
ld([Y,X])                       #22
st([vAC+1])                     #23
label('ldxw#24a')
ld(hi('ENTER'))                 #24
st([vCpuSelect])                #25
adda(1,Y)                       #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

label('stxw#3a')
ld([vPC+1],Y)                   #3
ld([vPC])                       #4
adda(2)                         #5
st([vPC],X)                     #6
ld([Y,X])                       #7
st([Y,Xpp])                     #8
adda([sysArgs+5])               #9
st([vTmp])                      #10
bmi('stxw#13a')                 #11
suba([sysArgs+5])               #12
ora([sysArgs+5])                #13
bmi('stxw#16a')                 #14
ld([Y,X])                       #15
bra('stxw#18a')                 #16
adda([sysArgs+6],Y)             #17
label('stxw#13a')
anda([sysArgs+5])               #13
bmi('stxw#16a')                 #14
ld([Y,X])                       #15
bra('stxw#18a')                 #16
adda([sysArgs+6],Y)             #17
label('stxw#16a')
adda(1)                         #16
adda([sysArgs+6],Y)             #17
label('stxw#18a')
ld([vTmp],X)                    #18
ld([vAC])                       #19
st([Y,Xpp])                     #20
ld([vAC+1])                     #21
bra('ldxw#24a')                 #22
st([Y,X])                       #23



#-----------------------------------------------------------------------
#
#   $1D00 ROM page 29: FSM for long multiplications and mulq
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM1D_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM1D_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8


#----------------------------------------
# MACX

label('macx#17')
ld(0)                           #17
st([sysArgs+4])                 #18
ld(hi('FSM1D_ENTER'))           #19
st([vCpuSelect])                #20
ld(1)                           #21
st([vAC+1])                     #22
anda([vAC])                     #23
bne(pc()+3)                     #24
bra(pc()+3)                     #25
ld('macx#3a')                   #26
ld('macx#3c')                   #26
st([fsmState])                  #27
bra('NEXT')                     #28
ld(-30/2)                       #29

label('macx#3a')
ld([sysArgs+0])                 #3 sysArgs[0..4]<<=1
bmi('macx#6aa')                 #4
adda(AC)                        #5
st([sysArgs+0])                 #6 b0 non-carry path
ld([sysArgs+1])                 #7
bmi('macx#10aa')                #8
nop()                           #9
label('macx#10a')
adda([sysArgs+1])               #10
st([sysArgs+1])                 #11 b1
ld([sysArgs+2])                 #12
bmi('macx#15aa')                #13
nop()                           #14
label('macx#15a')
adda([sysArgs+2])               #15
st([sysArgs+2])                 #16 b2
ld([sysArgs+3])                 #17
bra('macx#20aa')                #18
anda(0x80,X)                    #19

label('macx#6aa')
st([sysArgs+0])                 #6 b0 carry path
ld([sysArgs+1])                 #7
bpl('macx#10a')                 #8
adda(1)                         #9
label('macx#10aa')
adda([sysArgs+1])               #10
st([sysArgs+1])                 #11 b1
ld([sysArgs+2])                 #12
bpl('macx#15a')                 #13
adda(1)                         #14
label('macx#15aa')
adda([sysArgs+2])               #15
st([sysArgs+2])                 #16 b2
ld([sysArgs+3])                 #17
anda(0x80,X)                    #18
adda(1)                         #19
label('macx#20aa')
adda([sysArgs+3])               #20
st([sysArgs+3])                 #21 b3
ld([sysArgs+4])                 #22
adda(AC)                        #23
adda([X])                       #23
st([sysArgs+4])                 #25 b4
ld('macx#3b')                   #26
st([fsmState])                  #27
bra('NEXT')                     #28
ld(-30/2)                       #29

label('macx#3b')
ld([vAC+1])                     #3 vACH <<= 1
adda(AC)                        #4
st([vAC+1])                     #5
beq('macx#8b')                  #6 > finish
anda([vAC])                     #7
bne(pc()+3)                     #8
bra(pc()+3)                     #9
ld('macx#3a')                   #10 > loop
ld('macx#3c')                   #10 > add and loop
st([fsmState])                  #11
bra('NEXT')                     #12
ld(-14/2)                       #13
label('macx#8b')
ld([sysArgs+1])                 #8 restore sysArgs[0..3]
st([sysArgs+0])                 #9
ld([sysArgs+2])                 #10
st([sysArgs+1])                 #11
ld([sysArgs+3])                 #12
st([sysArgs+2])                 #13
ld([sysArgs+4])                 #14
st([sysArgs+3])                 #15
ld(hi('ENTER'))                 #16
st([vCpuSelect])                #17
adda(1,Y)                       #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20

label('macx#3c')
ld('macx#3d')                   #3 LAX += sysArgs[0..4]
st([fsmState])                  #4
ld([vLAX])                      #5
adda([sysArgs+0])               #6
st([vLAX])                      #7 b0
bmi('macx#10cc')                #8
suba([sysArgs+0])               #9
ora([sysArgs+0])                #10
bmi('macx#13cc')                #11
ld([vLAX+1])                    #12
label('macx#13c')
bra('macx#15cc')                #13
st([sysArgs+6])                 #14

label('macx#10cc')
anda([sysArgs+0])               #10
bpl('macx#13c')                 #11
ld([vLAX+1])                    #12
label('macx#13cc')
st([sysArgs+6])                 #13
adda(1)                         #14
label('macx#15cc')
adda([sysArgs+1])               #15
st([vLAX+1])                    #16 b1
bmi('macx#19ccc')               #17
ld([sysArgs+6])                 #18
ora([sysArgs+1])                #19
bmi('macx#22ccc')               #20
ld([vLAX+2])                    #21
label('macx#22cc')
bra('macx@24ccc')               #22
st([sysArgs+6])                 #23

label('macx#19ccc')
anda([sysArgs+1])               #19
bpl('macx#22cc')                #20
ld([vLAX+2])                    #21
label('macx#22ccc')
st([sysArgs+6])                 #22
adda(1)                         #23
label('macx@24ccc')
adda([sysArgs+2])               #24
st([vLAX+2])                    #25 b2
bra('NEXT')                     #26
ld(-28/2)                       #27

label('macx#3d')
ld('macx#3a')                   #3
st([fsmState])                  #4
ld([vLAX+2])                    #5 cont.
bmi('macx#8dd')                 #6
ld([sysArgs+6])                 #7
ora([sysArgs+2])                #8
bmi('macx#11dd')                #9
ld([vLAX+3])                    #10
label('macx#11d')
bra('macx#13dd')                #11
st([sysArgs+6])                 #12

label('macx#8dd')
anda([sysArgs+2])               #8
bpl('macx#11d')                 #9
ld([vLAX+3])                    #10
label('macx#11dd')
st([sysArgs+6])                 #11
adda(1)                         #12
label('macx#13dd')
adda([sysArgs+3])               #13
st([vLAX+3])                    #14 b3
bmi(pc()+4)                     #15
ld([sysArgs+6])                 #16
bra(pc()+4)                     #17
ora([sysArgs+3])                #18
nop()                           #17
anda([sysArgs+3])               #18
anda(0x80,X)                    #19
ld([vLAX+4])                    #20
adda([X])                       #21
adda([sysArgs+4])               #22
st([vLAX+4])                    #23
bra('NEXT')                     #24
ld(-26/2)                       #25


#----------------------------------------
# MULQ

label('mulq#13')
st([sysArgs+6])                 #13
ld([vAC])                       #14
st([sysArgs+4])                 #15
anda(0x80,X)                    #16
adda(AC)                        #17
st([vAC])                       #18
ld([vAC+1])                     #19
st([sysArgs+5])                 #20
adda(AC)                        #21
adda([X])                       #22
st([vAC+1])                     #23
ld('mulq#3a')                   #24
st([fsmState])                  #25
ld(hi('FSM1D_ENTER'))           #26
st([vCpuSelect])                #27
bra('NEXT')                     #28
ld(-30/2)                       #29

label('mulq#3a')
ld([sysArgs+6])                 #3
blt('mulq1#6a')                 #4
adda(AC)                        #5
beq('mulqz#8a')                 #6 mulq0
bgt('mulq00#9a')                #7
adda(AC)                        #8 mulq01
st([sysArgs+6])                 #9
ld([vAC])                       #10
adda([sysArgs+4])               #11
st([vAC])                       #12
bmi('mulq01#15a')               #13
suba([sysArgs+4])               #14
ora([sysArgs+4])                #15
bmi('mulq01c#18a')              #16
ld([vAC+1])                     #17
label('mulq01nc#18a')
adda([sysArgs+5])               #18
st([vAC+1])                     #19
bra('NEXT')                     #20
ld(-22/2)                       #21
label('mulq01#15a')
anda([sysArgs+4])               #15
bpl('mulq01nc#18a')             #16
ld([vAC+1])                     #17
label('mulq01c#18a')
adda([sysArgs+5])               #18
bra('mulq00#21a')               #19
adda(1)                         #20

label('mulq00#9a')
adda(AC)                        #9
st([sysArgs+6])                 #10
ld([vAC])                       #11
bmi(pc()+5)                     #12
suba([sysArgs+4])               #13
st([vAC])                       #14
bra(pc()+5)                     #15
ora([sysArgs+4])                #16
st([vAC])                       #14
nop()                           #15
anda([sysArgs+4])               #16
anda(0x80,X)                    #17
ld([vAC+1])                     #18
suba([sysArgs+5])               #19
suba([X])                       #20
label('mulq00#21a')
st([vAC+1])                     #21
bra('NEXT')                     #22
ld(-24/2)                       #23

label('mulqz#8a')
ld(hi('ENTER'))                 #8
st([vCpuSelect])                #9
adda(1,Y)                       #10
jmp(Y,'NEXTY')                  #11
ld(-14/2)                       #12

label('mulq1#6a')
blt('mulq11#8a')                #6
st([sysArgs+6])                 #7
ld([vAC])                       #8
anda(0x80,X)                    #9
adda(AC)                        #10
st([vAC])                       #11
ld([vAC+1])                     #12
adda(AC)                        #13
adda([X])                       #14
st([vAC+1])                     #15
bra('NEXT')                     #16
ld(-18/2)                       #17

label('mulq11#8a')
adda(AC)                        #8
st([sysArgs+6])                 #9
ld([vAC])                       #10
anda(0x80,X)                    #11
adda(AC)                        #12
st([vAC])                       #13
ld([vAC+1])                     #14
adda(AC)                        #15
adda([X])                       #16
st([vAC+1])                     #17
ld([vAC])                       #18
anda(0x80,X)                    #19
adda(AC)                        #20
st([vAC])                       #21
ld([vAC+1])                     #22
adda(AC)                        #23
adda([X])                       #24
st([vAC+1])                     #25
bra('NEXT')                     #26
ld(-28/2)                       #27


#-----------------------------------------------------------------------
#
#   $1e00 ROM page 30:  FSM for vCPU long ops
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM1E_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM1E_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8

# ----------------------------------------
# CMPLS CMPLU

label('cmpls#3a')
ld([vAC+1],Y)                   #3
ld([vAC])                       #4
adda(3,X)                       #5
ld([vLAC+3])                    #6 B3
xora([Y,X])                     #7
beq('cmpl#10a')                 #8 -> next byte
blt('cmpls#11')                 #9 -> different msb
xora([Y,X])                     #10
bra('cmpl#13')                  #11
suba([Y,X])                     #12
label('cmpls#11')
bra('cmpl#13')                  #11
ora(1)                          #12

label('cmplu#3a')
ld([vAC+1],Y)                   #3
ld([vAC])                       #4
adda(3,X)                       #5
ld([vLAC+3])                    #6 B3
xora([Y,X])                     #7
beq('cmpl#10a')                 #8 -> next byte
blt('cmpl#11')                  #9 -> different msb
xora([Y,X])                     #10
bra('cmpl#13')                  #11
suba([Y,X])                     #12
label('cmpl#11')
xora(0x80)                      #11
ora(1)                          #12
label('cmpl#13')
st([vAC+1])                     #13
ld(hi('ENTER'))                 #14
st([vCpuSelect])                #15
adda(1,Y)                       #16
jmp(Y,'NEXTY')                  #17
ld(-20/2)                       #18
label('cmpl#10a')
ld([vAC])                       #10 next byte
adda(2,X)                       #11
ld([vLAC+2])                    #12 B2
xora([Y,X])                     #13
beq('cmpl#16a')                 #14 -> next byte
blt('cmpl#17')                  #15 -> different msb
xora([Y,X])                     #16
bra('cmpl#19')                  #17
suba([Y,X])                     #18
label('cmpl#17')
xora(0x80)                      #17
ora(1)                          #18
label('cmpl#19')
st([vAC+1])                     #19
ld(hi('ENTER'))                 #20
st([vCpuSelect])                #21
adda(1,Y)                       #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24
label('cmpl#16a')
ld('cmpl#3b')                   #16 next byte
st([fsmState])                  #17
bra('NEXT')                     #18
ld(-20/2)                       #19

label('cmpl#3b')
ld([vAC+1],Y)                   #3
ld([vAC])                       #4
adda(1,X)                       #5
ld([vLAC+1])                    #6 B1
xora([Y,X])                     #7
beq('cmpl#10b')                 #8 -> next byte
blt('cmpl#11')                  #9 -> different msb
xora([Y,X])                     #10
bra('cmpl#13')                  #11
suba([Y,X])                     #12
label('cmpl#10b')
ld([vAC],X)                     #10 next byte
nop()                           #11
ld([vLAC])                      #12 B0
xora([Y,X])                     #13
beq('cmpl#16b')                 #14 -> equal!
blt('cmpl#17')                  #15 -> different msb
xora([Y,X])                     #16
bra('cmpl#19')                  #17
suba([Y,X])                     #18
label('cmpl#16b')
st([vAC])                       #16 equal!
st([vAC+1])                     #17
ld(hi('ENTER'))                 #18
st([vCpuSelect])                #19
adda(1,Y)                       #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

# ----------------------------------------
# LSLXA

label('lslxa#3a')
ld([vAC])                       #3
anda(0x3f)                      #4
suba(8)                         #5
blt('lslxa#8a')                 #6
st([vAC])                       #7
ld([vLAX+3])                    #8
st([vLAX+4])                    #9
ld([vLAX+2])                    #10
st([vLAX+3])                    #11
ld([vLAX+1])                    #12
st([vLAX+2])                    #13
ld([vLAX+0])                    #14
st([vLAX+1])                    #15
ld(0)                           #16
st([vLAX+0])                    #17
bra('NEXT')                     #18
ld(-20/2)                       #19

label('lslxa#8a')
anda(7)                         #8
bne('lslxa#11a')                #9
ld(hi('NEXTY'),Y)               #10
ld(hi('ENTER'))                 #11
st([vCpuSelect])                #12
jmp(Y,'NEXTY')                  #13
ld(-16/2)                       #14
label('lslxa#11a')
st([vAC])                       #11
ld('lslxa#3b')                  #12
st([fsmState])                  #13
bra('NEXT')                     #14
ld(-16/2)                       #15

label('lslxa#3b')
adda(min(0,maxTicks-40/2) )     #3
blt('NEXT')                     #4
ld(-6/2)                        #5
ld([vLAX])                      #6 b0
bmi('lslxa#9bb')                #7
adda([vLAX])                    #8
st([vLAX])                      #9
ld([vLAX+1])                    #10 b1
nop()                           #11
bmi('lslxa#14bb')               #12
label('lslxa#13b')
adda([vLAX+1])                  #13
st([vLAX+1])                    #14
ld([vLAX+2])                    #15 b2
nop()                           #16
bmi('lslxa#19bb')               #17
label('lslxa#18b')
adda([vLAX+2])                  #18
st([vLAX+2])                    #19
ld([vLAX+3])                    #20 b3
bra('lslxa#23bb')               #21
anda(0x80,X)                    #22

label('lslxa#9bb')
st([vLAX])                      #9
ld([vLAX+1])                    #10 b1
bpl('lslxa#13b')                #11
adda(1)                         #12
adda([vLAX+1])                  #13
label('lslxa#14bb')
st([vLAX+1])                    #14
ld([vLAX+2])                    #15 b2
bpl('lslxa#18b')                #16
adda(1)                         #17
adda([vLAX+2])                  #18
label('lslxa#19bb')
st([vLAX+2])                    #19
ld([vLAX+3])                    #20 b3
anda(0x80,X)                    #21
adda(1)                         #22
label('lslxa#23bb')
adda([vLAX+3])                  #23
st([vLAX+3])                    #24
ld([vLAX+4])                    #25 b4
adda([vLAX+4])                  #26
adda([X])                       #27
st([vLAX+4])                    #28
ld([vAC])                       #29 finished?
suba(1)                         #30
st([vAC])                       #31
bgt('NEXT')                     #32
ld(-34/2)                       #33
ld(hi('ENTER'))                 #34 exit
st([vCpuSelect])                #35
adda(1,Y)                       #36
jmp(Y,'NEXTY')                  #37
ld(-40/2)                       #38

# ----------------------------------------
# STFAC implementation

label('stfac#3a')
ld([vAC+1],Y)                   #3,21
ld([vFAE])                      #4
bne('stfac#7b')                 #5
ld([vAC],X)                     #6
st([vLAX])                      #7  zero!
st([vLAX+1])                    #8
st([vLAX+2])                    #9
st([vLAX+3])                    #10
st([vLAX+4])                    #11
ld('stfac#3b')                  #12
st([fsmState])                  #13
bra('NEXT')                     #14
ld(-16/2)                       #15

label('stfac#3b')
ld(1)                           #3
ld([vAC+1],Y)                   #4
ld([vAC],X)                     #5
ld([vFAE])                      #6
label('stfac#7b')
st([Y,Xpp])                     #7
ld([vAC])                       #8
anda(0xfc)                      #9
xora(0xfc)                      #10
beq('stfac#13b')                #11
ld([vFAS])                      #12 fast
ora(0x7f)                       #13
anda([vLAX+4])                  #14
st([Y,Xpp])                     #15
ld([vLAX+3])                    #16
st([Y,Xpp])                     #17
ld([vLAX+2])                    #18
st([Y,Xpp])                     #19
ld([vLAX+1])                    #20
st([Y,X])                       #21
ld(hi('ENTER'))                 #22
st([vCpuSelect])                #23
adda(1,Y)                       #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26

label('stfac#13b')
ora(0x7f)                       #13 slow!
anda([vLAX+4])                  #14
st([sysArgs+5])                 #15 next to save
ld(vLAX+4)                      #16
st([sysArgs+6])                 #17
ld('stfac#3c')                  #18
st([fsmState])                  #19
bra('NEXT')                     #20
ld(-22/2)                       #21

label('stfac#3c')
ld(1)                           #3 slow loop
adda([vAC])                     #4
st([vAC],X)                     #5
beq('stfac#3c')                 #6 ld(1)
bra(pc()+2)                     #7
ld(0)                           #8
adda([vAC+1])                   #9
st([vAC+1],Y)                   #10
ld([sysArgs+5])                 #11
st([Y,X])                       #12
ld([sysArgs+6])                 #13
suba(1)                         #14
st([sysArgs+6],X)               #15
xora(vLAX)                      #16
beq('stfac#19c')                #17
ld([X])                         #18
st([sysArgs+5])                 #19
bra('NEXT')                     #20
ld(-22/2)                       #21
label('stfac#19c')
nop()                           #19
ld(hi('ENTER'))                 #20
st([vCpuSelect])                #21
adda(1,Y)                       #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24



#-----------------------------------------------------------------------
#
#   $1f00 ROM page 31: vCPU stack ops
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)

# ALLOC implementation
label('alloc#13')
st([vTmp])                      #13
ld(hi('REENTER'),Y)             #14
ld([vSP+1])                     #15
bne('alloc#18')                 #16
ld([vSP])                       #17
adda([vTmp])                    #18
st([vSP])                       #19
jmp(Y,'REENTER')                #20
ld(-24/2)                       #21

label('alloc#18')
bge('alloc#20')                 #18 vSP16 version
adda([vTmp])                    #19
st([vSP])                       #20
ora([vTmp])                     #21
blt('alloc#24x')                #22
ld(1)                           #23
label('alloc#24')
adda([vSP+1])                   #24
st([vSP+1])                     #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27
label('alloc#20')
st([vSP])                       #20
anda([vTmp])                    #21
blt('alloc#24')                 #22
ld(0xff)                        #23
label('alloc#24x')
jmp(Y,'REENTER')                #24
ld(-28/2)                       #25

# Restarts
label('retry1f#20')
nop()                           #20
label('retry1f#21')
nop()                           #21
label('retry1f#22')
ld([vPC])                       #22
suba(2)                         #23
st([vPC])                       #24
ld(hi('REENTER'),Y)             #25
jmp(Y,'REENTER')                #26
ld(-30/2)                       #27

# PUSH implementation
label('push#13')
ld([vSP])                       #13
beq('push#16')                  #14
suba(2)                         #15
st([vSP],X)                     #16
ld([vLR])                       #17
st([Y,Xpp])                     #18
ld([vLR+1])                     #19
st([Y,Xpp])                     #20
ld([vPC])                       #21
suba(1)                         #22
st([vPC])                       #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28//2)                      #26
label('push#16')
ld([vTicks])                    #16 carry
adda(min(0,maxTicks-38/2))      #17
blt('retry1f#20')               #18
ld(0xfe)                        #19
st([vSP],X)                     #20
ld([vSP+1])                     #21
beq(pc()+3)                     #22
bra(pc()+3)                     #23
suba(1)                         #24
nop()                           #24
st([vSP+1],Y)                   #25
ld([vLR])                       #26
st([Y,Xpp])                     #27
ld([vLR+1])                     #28
st([Y,Xpp])                     #29
label('push#30')
ld([vPC])                       #30
suba(1)                         #31
st([vPC])                       #32
ld(hi('REENTER'),Y)             #33
jmp(Y,'REENTER')                #34
ld(-38//2)                      #35

# POP implementation
label('pop#13')
ld([vSP])                       #13
adda(2)                         #14
beq('pop#17')                   #15
suba(2,X)                       #16
st([vSP])                       #17
ld([Y,X])                       #18
st([Y,Xpp])                     #19
st([vLR])                       #20
ld([Y,X])                       #21
st([vLR+1])                     #22
ld([vPC])                       #23
suba(1)                         #24
st([vPC])                       #25
ld(hi('NEXTY'),Y)               #26
jmp(Y,'NEXTY')                  #27
ld(-30//2)                      #28
label('pop#17')
ld([vTicks])                    #17 carry
adda(min(0,maxTicks-38/2))      #18
blt('retry1f#21')               #19
ld([Y,X])                       #20
st([Y,Xpp])                     #21
st([vLR])                       #22
ld([Y,X])                       #23
st([vLR+1])                     #24
ld(0)                           #25
st([vSP])                       #26
ld([vSP+1])                     #27
beq('push#30')                  #28
adda(1)                         #29
st([vSP+1])                     #30
ld([vPC])                       #31
suba(1)                         #32
st([vPC])                       #33
ld(hi('NEXTY'),Y)               #34
jmp(Y,'NEXTY')                  #35
ld(-38//2)                      #36

# STLW implementation
label('stlw#13')
adda([vSP])                     #13
st([vTmp],X)                    #14
ld([vSP+1])                     #15
bne('stlw#18')                  #16
ld(AC,Y)                        #17
ld([vAC])                       #18
st([Y,Xpp])                     #19
ld([vAC+1])                     #20
st([Y,X])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

label('stlw#18')
ld([vTicks])                    #18 vSPL/vSPH version
adda(min(0,maxTicks-36/2))      #19
blt('retry1f#22')               #20
ld([vTmp])                      #21
bmi('stlw#24')                  #22
suba([vSP])                     #23
ora([vSP])                      #24
bmi('stlw#27c')                 #25
ld(1)                           #26
label('stlw#27nc')
bra('stlw#29')                  #27
ld([vAC])                       #28
label('stlw#24')
anda([vSP])                     #24
bpl('stlw#27nc')                #25
ld(1)                           #26
label('stlw#27c')
adda([vSP+1],Y)                 #27
ld([vAC])                       #28
label('stlw#29')
st([Y,Xpp])                     #29
ld([vAC+1])                     #30
st([Y,X])                       #31
ld(hi('NEXTY'),Y)               #32
jmp(Y,'NEXTY')                  #33
ld(-36/2)                       #34

# LDLW implementation
label('ldlw#13')
adda([vSP],X)                   #13
ld([vSP+1])                     #14
bne('ldlw#17')                  #15
ld(AC,Y)                        #16
ld([Y,X])                       #17
st([Y,Xpp])                     #18
st([vAC])                       #19
ld([Y,X])                       #20
st([vAC+1])                     #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

label('ldlw#17')
ld([vTicks])                    #17 vSPL/vSPH version
adda(min(0,maxTicks-38/2))      #18
blt('retry1f#21')               #19
ld([vTmp])                      #20
adda([vSP])                     #21
bmi('ldlw#24')                  #22
ld([vTmp])                      #23
ora([vSP])                      #24
bmi('ldlw#27c')                 #25
ld(1)                           #26
label('ldlw#27nc')
ld([Y,X])                       #27
st([Y,Xpp])                     #28
st([vAC])                       #29
ld([Y,X])                       #30
st([vAC+1])                     #31
ld(hi('NEXTY'),Y)               #32
jmp(Y,'NEXTY')                  #33
ld(-36/2)                       #34
label('ldlw#24')
anda([vSP])                     #24
bpl('ldlw#27nc')                #25
ld(1)                           #26
label('ldlw#27c')
adda([vSP+1],Y)                 #27
ld([Y,X])                       #28
st([Y,Xpp])                     #29
st([vAC])                       #30
ld([Y,X])                       #31
st([vAC+1])                     #32
ld(hi('REENTER'),Y)             #33
jmp(Y,'REENTER')                #34
ld(-38/2)                       #35

# STLAC implementation
label('stlac#19')
# ld([vTicks])
# ld([vAC+1],Y)
adda(min(0,maxTicks-34/2))      #19
blt('retry1f#22')               #20
ld([vAC],X)                     #21
ld([vLAC])                      #22
st([Y,Xpp])                     #23
ld([vLAC+1])                    #24
st([Y,Xpp])                     #25
ld([vLAC+2])                    #26
st([Y,Xpp])                     #27
ld([vLAC+3])                    #28
st([Y,X])                       #29
ld(hi('NEXTY'),Y)               #30
jmp(Y,'NEXTY')                  #31
ld(-34/2)                       #32

# LDLAC implementation
label('ldlac#17')
adda(min(0,maxTicks-38/2))      #17
blt('retry1f#20')               #18
ld([vAC+1],Y)                   #19
ld([vAC],X)                     #20
ld([Y,X])                       #21
st([vLAC])                      #22
st([Y,Xpp])                     #23
ld([Y,X])                       #24
st([vLAC+1])                    #25
st([Y,Xpp])                     #26
ld([Y,X])                       #27
st([vLAC+2])                    #28
st([Y,Xpp])                     #29
ld([Y,X])                       #30
st([vLAC+3])                    #31
ld(hi('NEXTY'),Y)               #32
jmp(Y,'NEXTY')                  #33
ld(-36/2)                       #34

# INCV implementation
label('incv#13')
st([vTmp],X)                    #13
ld(1)                           #14
adda([X])                       #15
beq('incv#18')                  #16
st([X])                         #17
ld(hi('NEXTY'),Y)               #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20
label('incv#18')
ld(1)                           #18
adda([vTmp],X)                  #19
adda([X])                       #20
st([X])                         #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# NEGV implementation
label('negv#13')
ld(0,Y)                         #13
ld(AC,X)                        #14
ld(0)                           #15
suba([Y,X])                     #16
bne('negv#19')                  #17
st([Y,Xpp])                     #18
bra('negv#21')                  #19
suba([Y,X])                     #20
label('negv#19')
ld([Y,X])                       #19
xora(0xff)                      #20
label('negv#21')
st([Y,X])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# RESET_v7 implementation

label('reset#17')
ld(min(0,maxTicks-88//2))       #17 serious margin
adda([vTicks])                  #18
blt('retry1f#21')               #19
nop()                           #20
ld(hi('softReset#24'),Y)        #21
jmp(Y,'softReset#24')           #22
nop()                           #23


#-----------------------------------------------------------------------
#
#   $2000 ROM page 32: misc
#
#-----------------------------------------------------------------------

align(0x100, size=0x100)


#----------------------------------------
# LUP implementation

# LUP on dev7rom runs 4 cycles behind earlier ROMS.
# Clearing [vAC+1] is now achieved before branching
# into the rom page instead of in the return suffix.
# This permits sys_Exec to consult the ROM tables
# without losing the contents of [vAC+1] and with
# enough time to increment the lup pointer.
label('lup#13')
ld([vAC+1],Y)                   #13
ld(vAC+1,X)                     #14
jmp(Y,251)                      #15
st(0,[X])                       #16 clear [vAC+1]

# The LUP return stub name 'lupReturn#19' is hardcoded in the
# trampoline code which cannot be changed because asm.py must
# remain able to compile older roms.
label('lupReturn#19')           # name hardcoded in the trampoline code
label('lupReturn#23')           # same name with the proper timing suffix
ld([vCpuSelect])                #23 to current interpreter
adda(1,Y)                       #24
ld(-28/2)                       #25
jmp(Y,'NEXT')                   #26 using NEXT
ld([vPC+1],Y)                   #27


#----------------------------------------
# SYS_Exec fsm entry

label('sys_Exec')
ld('se:exec')                   #18
st([fsmState])                  #19
ld(1)                           #20
st([sysFn])                     #21
ld(0)                           #22
st([sysFn+1])                   #23
nop()                           #24
ld(hi('FSM16_ENTER'))           #25 jumps into exec fsm
st([vCpuSelect])                #26
adda(1,Y)                       #27
jmp(Y,'NEXT')                   #28
ld(-30/2)                       #29


#----------------------------------------
# SYS_Unpack implementation

# This has been displaced to make space in page 6
# for native code fragments that use the shift table.
label('unpack#18')
adda(min(0,maxTicks-60/2))      #18
blt('unpack#21')                #19 restart
ld(soundTable>>8,Y)             #20
ld([sysArgs+2])                 #21 a[2]>>2
ora(0x03,X)                     #22
ld([Y,X])                       #23
st([sysArgs+3])                 #24 -> Pixel 3
ld([sysArgs+2])                 #25 (a[2]&3)<<4
anda(0x03)                      #26
adda(AC)                        #27
adda(AC)                        #28
adda(AC)                        #29
adda(AC)                        #30
st([sysArgs+2])                 #31
ld([sysArgs+1])                 #32 | a[1]>>4
ora(0x03,X)                     #33
ld([Y,X])                       #34
ora(0x03,X)                     #35
ld([Y,X])                       #36
ora([sysArgs+2])                #37
st([sysArgs+2])                 #38 -> Pixel 2
ld([sysArgs+1])                 #39 (a[1]&15)<<2
anda(0x0f)                      #40
adda(AC)                        #41
adda(AC)                        #42
st([sysArgs+1])                 #42
ld([sysArgs+0])                 #44 | a[0]>>6
ora(0x03,X)                     #45
ld([Y,X])                       #46
ora(0x03,X)                     #47
ld([Y,X])                       #48
ora(0x03,X)                     #49
ld([Y,X])                       #50
ora([sysArgs+1])                #51
st([sysArgs+1])                 #52 -> Pixel 1
ld([sysArgs+0])                 #53 a[1]&63
anda(0x3f)                      #54
st([sysArgs+0])                 #55 -> Pixel 0
ld(hi('NEXTY'),Y)               #56
jmp(Y,'NEXTY')                  #57
ld(-60/2)                       #58
label('unpack#21')
ld([vPC])                       #21
suba(2)                         #22
st([vPC])                       #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26


# ----------------------------------------
# SYS_DoubleDabble implementation

label('sys_DoubleDabble')
anda(0x80,X)                    #18
ld([X])                         #19
st([sysArgs+5])                 #20
ld([sysArgs+0])                 #21
st([vAC])                       #22
ld([sysArgs+1])                 #23
st([vAC+1])                     #24
ld('ddab#3a')                   #25
st([fsmState])                  #26 schedule fix in fsm22
ld(hi('FSM22_ENTER'))           #27
st([vCpuSelect])                #28
adda(1,Y)                       #29
jmp(Y,'NEXT')                   #30
ld(-32/2)                       #31


#----------------------------------------
# More vCPU opcodes

# SUBW implementation
label('subw#13')
ld(AC,X)                        #13 Address of low byte to be subtracted
adda(1)                         #14
st([vTmp])                      #15 Address of high byte to be subtracted
ld([vAC])                       #16
bmi('subw#19')                  #17
suba([X])                       #18
st([vAC])                       #19 Store low result
ora([X])                        #20 Carry in bit 7
anda(0x80,X)                    #21 Move carry to bit 0
ld([vAC+1])                     #22
suba([X])                       #23
ld([vTmp],X)                    #24
suba([X])                       #25
st([vAC+1])                     #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28
label('subw#19')
st([vAC])                       #19 Store low result
anda([X])                       #20 Carry in bit 7
anda(0x80,X)                    #21 Move carry to bit 0
ld([vAC+1])                     #22
suba([X])                       #23
ld([vTmp],X)                    #24
suba([X])                       #25
st([vAC+1])                     #26
jmp(Y,'NEXTY')                  #27
ld(-30/2)                       #28

# MOVW implementation
label('movw#16')
st([vTmp])                      #16
ld(min(0,maxTicks-36//2))       #17
adda([vTicks])                  #18
blt('movw#21')                  #19
ld([vPC])                       #20
adda(1)                         #21
st([vPC])                       #22
ld([X])                         #23
ld([vTmp],X)                    #24
st([vTmp])                      #25
ld([X])                         #26
ld([sysArgs+7],X)               #27
ld(0,Y)                         #28
st([Y,Xpp])                     #29
ld([vTmp])                      #30
st([Y,X])                       #31
ld(hi('NEXTY'),Y)               #32
jmp(Y,'NEXTY')                  #33
ld(-36/2)                       #34
label('movw#21')
suba(2)                         #21
ld(hi('REENTER_28'),Y)          #22
jmp(Y,'REENTER_28')             #23
st([vPC])                       #24

# MOVQB implementation
label('movqb#13')
ld([vPC+1],Y)                   #13
st([vTmp])                      #14
st([Y,Xpp])                     #15
ld([Y,X])                       #16
ld([vTmp],X)                    #17
st([X])                         #18
ld([vPC])                       #19
adda(1)                         #20
st([vPC])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# MOVQW implementation
label('movqw#13')
st([vTmp])                      #13
st([Y,Xpp])                     #14
ld([Y,X])                       #15
ld([vTmp],X)                    #16
ld(0,Y)                         #17
st([Y,Xpp])                     #18
ld(0)                           #19
st([Y,X])                       #20
ld([vPC])                       #21
adda(1)                         #22
st([vPC])                       #23
ld(hi('NEXTY'),Y)               #24
jmp(Y,'NEXTY')                  #25
ld(-28/2)                       #26

# SUBI implementation
label('subi#13')
ld(hi('NEXTY'),Y)               #13
ld([vAC])                       #14
bmi('.subi#17')                 #15
suba([vTmp])                    #16
st([vAC])                       #17 Store low result
ora([vTmp])                     #18 Carry in bit 7
bmi('.subi#21c')                #19
ld([vAC+1])                     #20
label('.subi#21nc')
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22
label('.subi#17')
st([vAC])                       #17 Store low result
anda([vTmp])                    #18 Carry in bit 7
bpl('.subi#21nc')               #19
ld([vAC+1])                     #20
label('.subi#21c')
suba(1)                         #21
st([vAC+1])                     #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# LDXW implementation
label('ldxw#13')
st([vTmp])                      #13
adda(1,X)                       #14
bra('ldxw#17')                  #15
ld('ldxw#3a')                   #16
label('ldxw#17')
st([fsmState])                  #17
ld([X])                         #18
st([sysArgs+6])                 #19
ld([vTmp],X)                    #20
ld([X])                         #21
st([sysArgs+5])                 #22
ld(hi('FSM1C_ENTER'))           #23
st([vCpuSelect])                #24
adda(1,Y)                       #25
jmp(Y,'NEXT')                   #26
ld(-28/2)                       #27

# STXW implementation
label('stxw#13')
st([vTmp])                      #13
adda(1,X)                       #14
bra('ldxw#17')                  #15
ld('stxw#3a')                   #16

# DBNE implementation
label('dbne#13')
#ld(AC,X)
ld([X])                         #13
suba(1)                         #14
st([X])                         #15
bne('dbne#18')                  #16
ld([vPC])                       #17
adda(1)                         #18
st([vPC])                       #19
ld(hi('NEXTY'),Y)               #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22
label('dbne#18')
adda(2,X)                       #18
ld([vPC+1],Y)                   #19
ld([Y,X])                       #20
label('dbne#21')
st([vPC])                       #21
ld(hi('NEXTY'),Y)               #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24

# ADDSV implementation
label('addsv#13')
st([vTmp])                      #13
ld([vPC+1],Y)                   #14
st([Y,Xpp])                     #15
ld([Y,X])                       #16
ld([vTmp],X)                    #17
adda([X])			#18
xora([X])                       #19
blt('addsv#22')                 #20 was bit7 swapped?
xora([X])                       #21
st([X])                         #22 no ==> no carry
ld([vPC])                       #23
adda(1)                         #24
st([vPC])                       #25
ld(hi('NEXTY'),Y)               #26 return to vcpu
jmp(Y,'NEXTY')                  #27 in 30 cycles
ld(-30/2)                       #28
label('addsv#22')
st([X])                         #22 yes ==> maybe carry
ld('addsv#3a')			#23
st([fsmState])			#24 schedule fix in fsm22
ld(hi('FSM21_ENTER'))	        #25
st([vCpuSelect])		#26
adda(1,Y)                       #27
jmp(Y,'NEXT')                   #28
ld(-30/2)			#29





#-----------------------------------------------------------------------
#
#   $2100 ROM page 33: VIRQ VSAVE VRESTORE
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM21_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM21_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8


# ----------------------------------------
# ADDSV continuation

label('addsv#3a')
ld([vPC+1],Y)                   #3 possible carry in addsv
ld([vPC])                       #4
adda(1)                         #5
st([vPC],X)                     #6
ld([Y,X])                       #7 asgument: address
st([vTmp])                      #8
st([Y,Xpp])                     #9
ld([Y,X])                       #10 argument: immediate
ld(0,Y)                         #11
ld([vTmp],X)                    #12
blt('addsv#15a')                #13
ld([Y,X])                       #14
st([Y,Xpp])                     #15 0 <= imm < 128
blt('addsv#18a-nc')             #16
ld(1)                           #17
label('addsv#18a-c')
adda([Y,X])                     #18 carry path
st([Y,X])                       #19
ld(hi('ENTER'))                 #20
st([vCpuSelect])                #21
adda(1,Y)                       #22
jmp(Y,'NEXTY')                  #23
ld(-26/2)                       #24
label('addsv#15a')
st([Y,Xpp])                     #15 -128 <= imm < 0
blt('addsv#18a-c')              #16
ld(0xff)                        #17
label('addsv#18a-nc')
ld(hi('ENTER'))                 #18 no carry path
st([vCpuSelect])                #19
adda(1,Y)                       #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22


# ---------------------------------------
# Context structure
#
# page+0xe0: vAC
#     +0xe2: vPC, vLR, vSP
#     +0xe8: vLAC, vT2, vT3
#     +0xf0: sysArgs[0-7]
#     +0xf8: sysFn
#     +0xfa: vFAS, vFAE, vLAX0
#     +0xfd: vCpuSelect
#     +0xfe: irqFlag
#     +0xff: irqMask

def vSave(off,*vars):
    for v in vars:
        ld([v])
        st([Y,off])
        off += 1

def vRest(off,*vars):
    for v in vars:
        ld([Y,off])
        st([v])
        off += 1

#----------------------------------------
# VIRQ

label('vIRQ#92')
ld([Y,vIrqCtx_v7])              #92
ld(AC,Y)                        #93
vSave(0xf7, fsmState)           #94 fsmState/sysArgs+7
vSave(0xfd, vCpuSelect)         #96 vCpuSelect
st([Y,0xff])                    #98 inUse
ld('vIRQ#159')                  #99
st([fsmState])                  #100
label('vIRQ#10')
vSave(0xe0,vAC,vAC+1,vPC,vPC+1) #101,10
vSave(0xe4,vLR,vLR+1,vSP,vSP+1) 
vSave(0xe8,vLAC,vLAC+1,vLAC+2,vLAC+3)
vSave(0xec,vT2,vT2+1,vT3,vT3+1) 
vSave(0xf0,sysArgs,sysArgs+1,sysArgs+2,sysArgs+3)
vSave(0xf4,sysArgs+4,sysArgs+5,sysArgs+6)
vSave(0xf8,sysFn,sysFn+1,vFAS,vFAE,vLAX)
bra([fsmState])                 #28+28+101=157,+10=66
ld(1,Y)                         #158,67
label('vIRQ#159')
ld([Y,vIRQ_v5])                 #159
suba(2)                         #160
st([vPC])                       #161
ld([Y,vIRQ_v5+1])               #162
st([vPC+1])                     #163
ld(hi('ENTER'))                 #164
st([vCpuSelect])                #165
wait(188-166-extra)             #166 (+extra)
jmp(Y,'vBlankFirst#190')        #188
ld([channel])                   #189


#----------------------------------------
# VSAVE

label('vsave#17')
ld([vAC],Y)                     #17
vSave(0xf7, fsmState)           #18 fsmState
vSave(0xfd, vCpuSelect)         #20 vCpuSelect
st([Y,0xff])                    #22 inUse
ld('vsave#3a')                  #23
st([fsmState])                  #24
ld(hi('FSM21_ENTER'))           #25
st([vCpuSelect])                #26
adda(1,Y)                       #27
jmp(Y,'NEXT')                   #28
ld(-30/2)                       #29

label('vsave#3a')
adda(min(0,maxTicks-74/2))      #3
blt('NEXT')                     #4
ld(-6/2)                        #5
ld([vAC],Y)                     #6
ld('vsave#68a')                 #7
bra('vIRQ#10')                  #8
st([fsmState])                  #9
label('vsave#68a')
ld(hi('ENTER'))                 #68
st([vCpuSelect])                #69
adda(1,Y)                       #70
jmp(Y,'NEXTY')                  #71
ld(-74/2)                       #72


#----------------------------------------
# VRESTORE

label('vrestore#17')
ld('vrestore#3a')               #17 jump to fsm21
st([fsmState])                  #18
ld([vAC],Y)                     #19
vRest(0xe2,vPC,vPC+1)           #20
ld(hi('FSM21_ENTER'))           #24
st([vCpuSelect])                #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('vrestore#6a')
bra('NEXT')                     #6
ld(-8/2)                        #7

label('vrestore#3a')
adda(min(0,maxTicks-58/2))      #3
blt('vrestore#6a')              #4
ld([vAC],Y)                     #5
ld('vrestore#3b')               #6
st([fsmState])                  #7
vRest(0xe4,vLR,vLR+1,vSP,vSP+1)
vRest(0xe8,vLAC,vLAC+1,vLAC+2,vLAC+3)
vRest(0xec,vT2,vT2+1,vT3,vT3+1)
vRest(0xf0,sysArgs,sysArgs+1,sysArgs+2)
vRest(0xf3,sysArgs+3,sysArgs+4,sysArgs+5,sysArgs+6)
vRest(0xf8,sysFn,sysFn+1,vFAS,vFAE,vLAX)
bra('NEXT')                     #8+24+24=56
ld(-58/2)                       #57

label('vrestore#3b')
ld([frameCount])                #3
adda([vAC+1])                   #4
st([frameCount])                #5
bmi('vrestore#8b')              #6
suba([vAC+1])                   #7
ora([vAC+1])                    #8
bmi('vrestore#11b-c')           #9
ld([vAC],Y)                     #10
label('vrestore#11b-nc')
bra('vrestore#13b')             #11
nop()                           #12
label('vrestore#8b')
anda([vAC+1])                   #8
bpl('vrestore#11b-nc')          #9
ld([vAC],Y)                     #10
label('vrestore#11b-c')
ld(0xff)                        #11
st([frameCount])                #12
label('vrestore#13b')
vRest(0xe0,vAC,vAC+1)           #13-16
vRest(0xf7,fsmState)            #17-18
ld(0)                           #19
st([Y,0xff])                    #20 mark as unused
ld([Y,0xfd])                    #21 saved vCpuSelect
st([vCpuSelect],Y)              #22
ld([vTicks])                    #23
adda(-24/2-v6502_adjust)        #24 enough time for this and another instruction
blt('vrestore#27b')             #25 possibly a v6502 instruction?
ld([vTicks])                    #26
adda(-30/2)                     #27 yes: enter interpreter
jmp(Y,'ENTER')                  #28
nop()                           #29-30=-1
label('vrestore#27b')
ld(hi('RESYNC'),Y)              #27 no: resync
jmp(Y,'RESYNC')                 #28
adda(maxTicks-26//2)            #29-26=3




#-----------------------------------------------------------------------
#
#   $2200 ROM page 34: SYS_DoubleDabble, FILL_v7
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM22_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM22_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8



# ----------------------------------------
# SYS_DoubleDabble continuation

label('ddab#3a')
ld('ddab#3b')                   #3
st([fsmState])                  #4
ld([vAC])                       #5
xora([sysArgs+2])               #6
bne('ddab#9a')                  #7
ld([vAC+1])                     #8
xora([sysArgs+3])               #9
bne('ddab#12a')                 #10
ld([sysArgs+5])                 #11
bne('ddab#14a')                 #12
ld(hi('ENTER'))                 #13
st([vCpuSelect])                #14
adda(1,Y)                       #15
jmp(Y,'REENTER')                #16
ld(-20/2)                       #17
label('ddab#9a')
wait(12-9)                      #9
label('ddab#12a')
ld('ddab#3c')                   #12
st([fsmState])                  #13
label('ddab#14a')
ld([vAC])                       #14 vAC-=1
beq('ddab#17a')                 #15
suba(1)                         #16
st([vAC])                       #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('ddab#17a')
st([vAC])                       #17
ld([vAC+1])                     #18
suba(1)                         #19
st([vAC+1])                     #20
nop()                           #21
bra('NEXT')                     #22
ld(-24/2)                       #23

label('ddab#3b')
ld([vAC])                       #3 extend
st([sysArgs+2],X)               #4
ld([vAC+1])                     #5
st([sysArgs+3],Y)               #6
st(1,[Y,X])                     #7
ld(hi('ENTER'))                 #8
st([vCpuSelect])                #9
adda(1,Y)                       #10
jmp(Y,'NEXTY')                  #11
ld(-14/2)                       #12

label('ddab#3c')
ld('ddab#3a')                   #3
st([fsmState])                  #4
ld(sysArgs+5,X)                 #5
ld([sysArgs+5])                 #6 dabble
st(1,[X])                       #7
ld([vAC],X)                     #8
ld([vAC+1],Y)                   #9
adda([Y,X])                     #10 double
adda([Y,X])                     #11
st([Y,X])                       #12
suba([sysArgs+4])               #13
blt('ddab#16c')                 #14
nop()                           #15
bra('ddab#18c')                 #16
st([Y,X])                       #17
label('ddab#16c')
ld(sysArgs+5,X)                 #16
st(0,[X])                       #17
label('ddab#18c')
bra('NEXT')                     #18
ld(-20/2)                       #19



# ----------------------------------------
# FILL implementation


label('fsm22op0#17')
st([fsmState])                  #17
ld(hi('FSM22_ENTER'))           #18
st([vCpuSelect])                #19
bra('NEXT')                     #20
ld(-22/2)                       #21

# vT3=vv vT2=yyxx vAC=hhww
# sysArgs[45]=xcnt ycnt

label('fill#3a')
ld(fsmState,X)                  #3  Peak 60 bytes/scanline
st('fill#3d',[X])               #4
ld('fill#3c')                   #5
st([sysArgs+6])                 #6
ld([vAC+1])                     #7
st([sysArgs+5])                 #8
adda([vT2+1])                   #9
label('fill#10a')
suba(1)                         #10
st([vT2+1],Y)                   #11
ld([vAC])                       #12
anda(1)                         #13
beq('fill#16a')                 #14 -> even width
xora([vAC])                     #15
beq('fill#18a')                 #16 -> vline
st([sysArgs+4])                 #17
st('fill#3b',[X])               #18 odd w
adda([vT2],X)                   #19
ld([vT3])                       #20
st([Y,X])                       #21
bra('NEXT')                     #22
ld(-24/2)                       #23
label('fill#16a')
st([sysArgs+4])                 #16 even w
st('fill#3b',[X])               #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('fill#18a')
bra('NEXT')                     #18 vline
ld(-20/2)                       #19

label('fill#3b')
ld([sysArgs+4])                 #3 
ble('fill#6b')                  #4 -> burst12
suba(12)                        #5
bge('fill#8b')                  #6 -> burst12
ld([vT2+1],Y)                   #7
ld([sysArgs+6])                 #8 final 2,4,6,8,10
st([fsmState])                  #9
ld([sysArgs+4])                 #10
adda(AC)                        #11
adda(pc())                      #12
ld([vT2],X)                     #13
bra(AC)                         #14 dispatch!
ld([vT3])                       #15
label('fill#16b_2')
st([Y,Xpp])                     #16 !final 2
st([Y,Xpp])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('fill#16b_4')
nop()                           #16 !final 4
bra(pc()+1)                     #17
nop()                           #18,19
bra('fill#22b_4')               #20
label('fill#16b_6')
nop()                           #16 !final 6
nop()                           #17
bra('fill#20b_6')               #18
nop()                           #19
label('fill#16b_8')
bra('fill#18b_8')               #16 !final 8
nop()                           #17
label('fill#14b_12')
st([Y,Xpp])                     #14 write 12
st([Y,Xpp])                     #15
label('fill#16b_10')
st([Y,Xpp])                     #16 !final10
st([Y,Xpp])                     #17
label('fill#18b_8')
st([Y,Xpp])                     #18
st([Y,Xpp])                     #19
label('fill#20b_6')
st([Y,Xpp])                     #20
st([Y,Xpp])                     #21
label('fill#22b_4')
st([Y,Xpp])                     #22
st([Y,Xpp])                     #23
st([Y,Xpp])                     #24
st([Y,Xpp])                     #25
bra('NEXT')                     #26
ld(-28/2)                       #27
label('fill#6b')
nop()                           #6
ld([vT2+1],Y)                   #7
label('fill#8b')
beq('fill#10b')                 #8 burst12, >=12
adda([vT2],X)                   #9
bra('fill#12b')                 #10 nonfinal 12
st([sysArgs+4])                 #11
label('fill#10b')
ld([sysArgs+6])                 #10 final 12
st([fsmState])                  #11
label('fill#12b')
bra('fill#14b_12')              #12
ld([vT3])                       #13

label('fill#3c')
ld(fsmState,X)                  #3 next row
ld([sysArgs+5])                 #4
suba(1)                         #5
beq('fill#8c')                  #6
st([sysArgs+5])                 #7
bra('fill#10a')                 #8
ld([vT2+1])                     #9
label('fill#8c')
ld(hi('ENTER'))                 #8  exit
st([vCpuSelect])                #9
adda(1,Y)                       #10
jmp(Y,'NEXTY')                  #11
ld(-14/2)                       #12

label('fill#3d')
ld([sysArgs+5])                 #3 vertical line
blt('fill#6d')                  #4
suba(4)                         #5
bgt('fill#8d')                  #6
ld([vT2],X)                     #7 
ld([vT2+1],Y)                   #8 <= 4 left
adda(3)                         #9
st([sysArgs+5])                 #10
ld([vT3])                       #11
st([Y,X])                       #12
ld([sysArgs+5])                 #13
beq('fill#16d')                 #14 -> exit
ld([vT2+1])                     #15
suba(1)                         #16
st([vT2+1])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('fill#16d')
ld(hi('ENTER'))                 #16  exit
st([vCpuSelect])                #17
adda(1,Y)                       #18
jmp(Y,'NEXTY')                  #19
ld(-22/2)                       #20
label('fill#6d')
nop()                           #6 >= 128 left
ld([vT2],X)                     #7
label('fill#8d')
st([sysArgs+5])                 #8 > 4 left
ld([vT2+1],Y)                   #9
ld([vT3])                       #10
st([Y,X])                       #11
ld([vT2+1])                     #12
suba(1,Y)                       #13
ld([vT3])                       #14
st([Y,X])                       #15
ld([vT2+1])                     #16
suba(2,Y)                       #17
ld([vT3])                       #18
st([Y,X])                       #19
ld([vT2+1])                     #20
suba(3,Y)                       #21
suba(4)                         #22
st([vT2+1])                     #23
ld([vT3])                       #24
st([Y,X])                       #25
bra('NEXT')                     #26
ld(-28/2)                       #27




#-----------------------------------------------------------------------
#
#   $2300 ROM page 35: 
#
#-----------------------------------------------------------------------

fillers(until=0xff)
label('FSM23_ENTER')
bra(pc()+4)                     #0
align(0x100, size=0x100)
bra([fsmState])                 #1
assert (pc() & 255) == (symbol('NEXT') & 255)
label('FSM23_NEXT')
adda([vTicks])                  #0
bge([fsmState],warn=False)      #1
st([vTicks])                    #2
adda(maxTicks)                  #3
bgt(pc()&255)                   #4
suba(1)                         #5
ld(hi('vBlankStart'),Y)         #6
jmp(Y,[vReturn])                #7
ld([channel])                   #8



# ----------------------------------------
# BLIT implementation

# vT2 : dsty,dstx
# vT3 : srcy,srcx
# vAC : h,w

label('blit#17')
ld('blit#3a')                   #17
st([fsmState])                  #18
ld(hi('FSM23_ENTER'))           #19
st([vCpuSelect])                #20
adda(1,Y)                       #21 
jmp(Y,'NEXT')                   #22 bra?
ld(-24/2)                       #23

# LAC sysArgs23 : buffer
# sysArgs6      : nxtrow state
# sysArgs45     : xctr yctr

label('blit#3a')
ld([vAC+1])                     #3
st([sysArgs+5])                 #4
ld([vAC])                       #5
st([sysArgs+4])                 #6
ld([vT2+1])                     #7 Simplified for h<128
suba([vT3+1])                   #8
beq('blit#11a')                 #9  -> dsty = srcy
blt('blit#12a')                 #10 -> dsty < srcy
# dsty > srcy
nop()                           #11 
ld([vT2+1])                     #12 backwardx backwardy
adda([vAC+1])                   #13 
suba(1)                         #14
st([vT2+1])                     #15 dsty += h-1
ld([vT3+1])                     #16
adda([vAC+1])                   #17
suba(1)                         #18
st([vT3+1])                     #19 srcy += w-1
ld('blit#3e')                   #20
st([sysArgs+6])                 #21 use backwardy
ld('blit#3c')                   #22
st([fsmState])                  #23 -> backwardx
bra('NEXT')                     #24
ld(-26/2)                       #25

# dsty < srcy
label('blit#12a')
ld('blit#3f')                   #12 forwardy backwardx
st([sysArgs+6])                 #13
ld('blit#3c')                   #14
st([fsmState])                  #15
bra('NEXT')                     #16
ld(-18/2)                       #17
# dsty == srcy
label('blit#11a')
ld('blit#3f')                   #11 set forwardy
st([sysArgs+6])                 #12
ld([vT3])                       #13
suba([vT2])                     #14 - backwardx is possible if
xora([vAC])                     #15      w <= srcx - dstx
blt('blit#18a')                 #16       unsigned bytes
xora([vAC])                     #17
suba([vAC])                     #18 dstx-srcx-w
blt('blit#21a-f')               #19
ld(fsmState,X)                  #20
label('blit#21a-b')
st('blit#3c',[X])               #21 forwardy backwardx
bra('NEXT')                     #22
ld(-24/2)                       #23
label('blit#18a')
ld([vAC])                       #18
bge('blit#21a-b')               #19
ld(fsmState,X)                  #20
label('blit#21a-f')
st('blit#3g',[X])               #21 forwardy forwardx
bra('NEXT')                     #22
ld(-24/2)                       #23

label('blit#3c')
ld('blit#3d')                   #3 backwardx row
st([fsmState])                  #4 peak 15bytes/scanline
ld([vT3+1],Y)                   #5
ld([sysArgs+4])                 #6
suba(6)                         #7
adda([vT3],X)                   #8
ld([Y,X])                       #9
st([Y,Xpp])                     #10
st([sysArgs+3])                 #11
ld([Y,X])                       #12
st([Y,Xpp])                     #13
st([sysArgs+2])                 #14
ld([Y,X])                       #15
st([Y,Xpp])                     #16
st([vLAC+3])                    #17
ld([Y,X])                       #18
st([Y,Xpp])                     #19
st([vLAC+2])                    #20
ld([Y,X])                       #21
st([Y,Xpp])                     #22
st([vLAC+1])                    #23
ld([Y,X])                       #24
st([vLAC+0])                    #25
bra('NEXT')                     #26
ld(-28/2)                       #27

label('blit#3d')
ld([sysArgs+4])                 #3 backwardx row cont.
ble('blit#6d')                  #4
suba(6)                         #5
bge('blit#8d')                  #6
ld([vT2+1],Y)                   #7
ld([sysArgs+6])                 #8 final
st([fsmState])                  #9
ld([sysArgs+4])                 #10  0 < len < 6
adda(AC)                        #11
adda(AC)                        #12
adda(pc()-1)                    #13
bra(AC)                         #14 dispatch!
ld([vT2],X)                     #15
label('blit#16d_1')
ld([vLAC+0])                    #16 !final1
st([Y,Xpp])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('blit#16d_2')
nop()                           #16 !final2
bra(pc()+1)                     #17
nop()                           #18,19
bra('blit#22d_2')               #20
label('blit#16d_3')
nop()                           #16 !final3
nop()                           #17
bra('blit#20d_3')               #18
nop()                           #19
label('blit#16d_4')
bra('blit#18d_4')               #16 !final4
nop()                           #17
label('blit#14d_6')
ld([sysArgs+3])                 #14
st([Y,Xpp])                     #15
label('blit#16d_5')
ld([sysArgs+2])                 #16 !final5
st([Y,Xpp])                     #17
label('blit#18d_4')
ld([vLAC+3])                    #18
st([Y,Xpp])                     #19
label('blit#20d_3')
ld([vLAC+2])                    #20
st([Y,Xpp])                     #21
label('blit#22d_2')
ld([vLAC+1])                    #22
st([Y,Xpp])                     #23
ld([vLAC+0])                    #24
st([Y,Xpp])                     #25
bra('NEXT')                     #26
ld(-28/2)                       #27
# burst6
label('blit#6d')
nop()                           #6 burst 6 >=128
ld([vT2+1],Y)                   #7
label('blit#8d')
st([sysArgs+4])                 #8 burst 6
bne('blit#11d')                 #9
adda([vT2],X)                   #10
ld([sysArgs+6])                 #11 - final
bra('blit#14d_6')               #12
st([fsmState])                  #13
label('blit#11d')
ld('blit#3c')                   #11 - nonfinal
bra('blit#14d_6')               #12
st([fsmState])                  #13

label('blit#3e')
nop()                           #3 backwardy 
ld('blit#3c')                   #4 -> next is backwardx
st([fsmState])                  #5 backwardy
ld([sysArgs+5])                 #6
suba(1)                         #7
beq('blit#10e')                 #8
st([sysArgs+5])                 #9
ld([vAC])                       #10
st([sysArgs+4])                 #11
ld([vT2+1])                     #12
suba(1)                         #13
st([vT2+1])                     #14
ld([vT3+1])                     #15
suba(1)                         #16
st([vT3+1])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('blit#10e')
ld(hi('ENTER'))                 #10  exit
st([vCpuSelect])                #11
adda(1,Y)                       #12
jmp(Y,'NEXTY')                  #13
ld(-16/2)                       #14

label('blit#3f')
nop()                           #3 forwardy
ld('blit#3c')                   #4 -> next is backwardx
label('blit#5f')
st([fsmState])                  #5 forwardy
ld([sysArgs+5])                 #6
suba(1)                         #7
beq('blit#10f')                 #8
st([sysArgs+5])                 #9
ld([vAC])                       #10
st([sysArgs+4])                 #11
ld([vT2+1])                     #12
adda(1)                         #13
st([vT2+1])                     #14
ld([vT3+1])                     #15
adda(1)                         #16
st([vT3+1])                     #17
bra('NEXT')                     #18
ld(-20/2)                       #19
label('blit#10f')
ld([vT2+1])                     #10 restore srcy,dsty
suba([vAC+1])                   #11
adda(1)                         #12
st([vT2+1])                     #13
ld([vT3+1])                     #14
suba([vAC+1])                   #15
adda(1)                         #16
st([vT3+1])                     #17
ld(hi('ENTER'))                 #18  exit
st([vCpuSelect])                #19
adda(1,Y)                       #20
jmp(Y,'NEXTY')                  #21
ld(-24/2)                       #22

label('blit#3g')
ld([sysArgs+4])                 #3 forwardx same row
anda(1)                         #4 peak 10bytes/scanline
bne('blit#7g')                  #5
ld([vT3+1],Y)                   #6
ld([vAC])                       #7
suba([sysArgs+4])               #8
adda([vT3],X)                   #9
ld([Y,X])                       #10
st([sysArgs+2])                 #11
st([Y,Xpp])                     #12
ld([Y,X])                       #13
st([sysArgs+3])                 #14
ld([vAC])                       #15
suba([sysArgs+4])               #16
adda([vT2],X)                   #17
ld([sysArgs+2])                 #18
st([Y,Xpp])                     #19
ld([sysArgs+3])                 #20
st([Y,Xpp])                     #21
ld([sysArgs+4])                 #22
suba(2)                         #23
beq('blit#26g')                 #24
st([sysArgs+4])                 #25
bra('NEXT')                     #26
ld(-28/2)                       #27
label('blit#26g')
ld('blit#3h')                   #26
st([fsmState])                  #27
bra('NEXT')                     #28
ld(-30/2)                       #29
label('blit#7g')
ld([vAC])                       #7
suba([sysArgs+4])               #8
adda([vT3],X)                   #9
ld([Y,X])                       #10
st([sysArgs+2])                 #11
ld([vAC])                       #12
suba([sysArgs+4])               #13
adda([vT2],X)                   #14
ld([sysArgs+2])                 #15
st([Y,Xpp])                     #16
ld([sysArgs+4])                 #17
suba(1)                         #18
st([sysArgs+4])                 #19
bne('NEXT')                     #20
ld(-22/2)                       #21
ld('blit#3h')                   #22
st([fsmState])                  #23
bra('NEXT')                     #24
ld(-26/2)                       #25

label('blit#3h')
bra('blit#5f')                  #3 forwardy forwardx
ld('blit#3g')                   #4 slower!


#-----------------------------------------------------------------------
#
#  End of Core
#
#-----------------------------------------------------------------------

align(0x100)

disableListing()

#-----------------------------------------------------------------------
#
#  Start of storage area
#
#-----------------------------------------------------------------------

# Export some zero page variables to GCL
# These constants were already loaded from interface.json.
# We're redefining them here to get a consistency check.
define('memSize',    memSize)
for i in range(3):
  define('entropy%d' % i, entropy+i)
define('videoY',       videoY)
define('frameCount',   frameCount)
define('serialRaw',    serialRaw)
define('buttonState',  buttonState)
define('xoutMask',     xoutMask)
define('vPC',          vPC)
define('vAC',          vAC)
define('vACH',         vAC+1)
define('vLR',          vLR)
define('vSP',          vSP)
define('vSP_v7',       vSP)
define('vSPL_v7',      vSP)
define('vSPH_v7',      vSP+1)
define('vTmp',         vTmp)      # Not in interface.json
define('romType',      romType)
define('sysFn',        sysFn)
for i in range(8):
  define('sysArgs%d' % i, sysArgs+i)
define('soundTimer',   soundTimer)
define('ledState_v2',  ledState_v2)
define('userVars',     userVars)
define('userVars_v4',  userVars_v4)
define('userVars_v5',  userVars_v5)
define('userVars_v6',  userVars_v6)
define('userVars_v7',  userVars_v7)
define('userVars2',    userVars2)
define('userVars2_v4', userVars2_v4)
define('userVars2_v5', userVars2_v5)
define('userVars2_v6', userVars2_v6)
define('vFAS_v7'    ,vFAS)
define('vFAE_v7'    ,vFAE)
define('vLAX_v7'    ,vLAX)
define('vLAC_v7'    ,vLAC)
define('vT2_v7'     ,vT2)
define('vT3_v7'     ,vT3)
define('userVars2_v7', userVars2_v7)
define('videoTable', videoTable)
define('ledTimer_v7',ledTimer)
define('ledTempo_v7',ledTempo)
define('vIRQ_v5',    vIRQ_v5)
define('ctrlBits_v5',ctrlBits)
define('videoTop_v5',videoTop_v5)
define('userCode',   userCode)
define('soundTable', soundTable)
define('screenMemory',screenMemory)
define('vReset',     vReset)
define('wavA',       wavA)
define('wavX',       wavX)
define('keyL',       keyL)
define('keyH',       keyH)
define('oscL',       oscL)
define('oscH',       oscH)
define('maxTicks',   maxTicks)
define('v6502_PC',   v6502_PC)
define('v6502_PCL',  v6502_PCL)
define('v6502_PCH',  v6502_PCH)
define('v6502_A',    v6502_A)
define('v6502_X',    v6502_X)
define('v6502_Y',    v6502_Y)
define('qqVgaWidth', qqVgaWidth)
define('qqVgaHeight',qqVgaHeight)
define('buttonRight',buttonRight)
define('buttonLeft', buttonLeft)
define('buttonDown', buttonDown)
define('buttonUp',   buttonUp)
define('buttonStart',buttonStart)
define('buttonSelect',buttonSelect)
define('buttonB',    buttonB)
define('buttonA',    buttonA)

# XXX This is a hack (trampoline() is probably in the wrong module):
define('vPC+1',      vPC+1)

#-----------------------------------------------------------------------
#       Embedded programs -- import and convert programs and data
#-----------------------------------------------------------------------

def basicLine(address, number, text):
  """Helper to encode lines for TinyBASIC"""
  head = [] if number is None else [number&255, number>>8]
  body = [] if text is None else [ord(c) for c in text] + [0]
  s = head + body
  assert len(s) > 0
  for i, byte in enumerate([address>>8, address&255, len(s)]+s):
    comment = repr(chr(byte)) if i >= 3+len(head) else None
    program.putInRomTable(byte, comment=comment)

#-----------------------------------------------------------------------

lastRomFile = ''

def insertRomDir(name):
  global lastRomFile
  if name[0] != '_':                    # Mechanism for hiding files
    if pc()&255 >= 251-14:              # Prevent page crossing
      trampoline()
    s = lastRomFile[0:8].ljust(8,'\0')  # Cropping and padding
    if len(lastRomFile) == 0:
      lastRomFile = 0
    for i in range(8):
      st(ord(s[i]), [Y,Xpp])            #25-32
      C(repr(s[i]))
    ld(lo(lastRomFile))                 #33
    st([vAC])                           #34
    ld(hi(lastRomFile))                 #35
    ld(hi('.sysDir#39'),Y)              #36
    jmp(Y,'.sysDir#39')                 #37
    st([vAC+1])                         #38
    lastRomFile = name

#-----------------------------------------------------------------------
#       Embedded programs must be given on the command line
#-----------------------------------------------------------------------

if pc()&255 >= 251:                     # Don't start in a trampoline region
  align(0x100)

for application in argv[1:]:
    print()

    # Determine label
    if '=' in application:
        # Explicit label given as 'label=filename'
        name, application = application.split('=', 1)
    else:
        # Label derived from filename itself
        name = application.rsplit('.', 1)[0] # Remove extension
        name = name.rsplit('/', 1)[-1]       # Remove path
    print('Processing file %s label %s' % (application, name))

    C('+-----------------------------------+')
    C('| %-33s |' % application)
    C('+-----------------------------------+')

    # Pre-compiled GT1 files
    if application.endswith(('.gt1', '.gt1x', '.gt1z')):
        print('Load type .gt1 at $%04x' % pc())
        with open(application, 'rb') as f:
            raw = bytearray(f.read())
        if pc() & 255 > 250:
            align(0x100,250)
        insertRomDir(name)
        label(name)
        for byte in raw:
            ld(byte)
            if pc() & 255 == 251:
                trampoline()

    # GCL files
    #----------------------------------------------------------------
    #  !!! GCL programs using *labels* "_L=xx" must be cautious !!!
    # Those labels end up in the same symbol table as the ROM build,
    # and name clashes cause havoc. It's safer to precompile such
    # applications into .gt1/.gt1x files. (This warning doesn't apply
    # to ordinary GCL variable names "xx A=".)
    #----------------------------------------------------------------
    elif application.endswith('.gcl'):
        print('Compile type .gcl at $%04x' % pc())
        insertRomDir(name)
        label(name)
        program = gcl.Program(name, romName=DISPLAYNAME)
        program.org(userCode)
        zpReset(userVars)
        for line in open(application).readlines():
            program.line(line)
        # finish
        program.end()            # 00
        program.putInRomTable(2) # exech
        program.putInRomTable(0) # execl

    # Application-specific SYS extensions
    elif application.endswith('.py'):
        print('Include type .py at $%04x' % pc())
        label(name)
        importlib.import_module(name)

    # For Pictures
    elif application.endswith(('/packedPictures.rgb')):
        print(('Convert type packedPictures.rgb at $%04x' % pc()))
        f = open(application, 'rb')
        raw = bytearray(f.read())
        f.close()
        label(name)
        for i in range(len(raw)):
            if i&255 < 251:
                ld(raw[i])
            elif pc()&255 == 251:
                trampoline()

    # Other files
    elif application.endswith('.gtb'):
        highlight('Error: Please use Utils/gtbtogt1.py')
    elif application.endswith('.rgb'):
        highlight('Error: Please use Utils/imgtogt1.py')
    else:
        assert False

    C('End of %s, size %d' % (application, pc() - symbol(name)))
    print(' Size %s' % (pc() - symbol(name)))

#-----------------------------------------------------------------------
# ROM directory
#-----------------------------------------------------------------------

# SYS_ReadRomDir implementation

if pc()&255 > 251 - 28:         # Prevent page crossing
  trampoline()
label('sys_ReadRomDir')
beq('.sysDir#20')               #18
ld(lo(sysArgs),X)               #19
ld(AC,Y)                        #20 Follow chain to next entry
ld([vAC])                       #21
suba(14)                        #22
jmp(Y,AC)                       #23
#ld(hi(sysArgs),Y)              #24 Overlap
#
label('.sysDir#20')
ld(hi(sysArgs),Y)               #20,24 Dummy
ld(lo('.sysDir#25'))            #21 Go to first entry in chain
ld(hi('.sysDir#25'),Y)          #22
jmp(Y,AC)                       #23
ld(hi(sysArgs),Y)               #24
label('.sysDir#25')
insertRomDir(lastRomFile)       #25-38 Start of chain
label('.sysDir#39')
ld(hi('REENTER'),Y)             #39 Return
jmp(Y,'REENTER')                #40
ld(-44/2)                       #41

print()

#-----------------------------------------------------------------------
# End of embedded applications
#-----------------------------------------------------------------------

if pc()&255 > 0:
  trampoline()

#-----------------------------------------------------------------------
# Finish assembly
#-----------------------------------------------------------------------
end()
writeRomFiles(ROMNAME or argv[0])
