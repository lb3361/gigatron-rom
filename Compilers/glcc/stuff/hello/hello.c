
#include <stdio.h>

#ifdef USE_RAWCONSOLE
# include <gigatron/console.h>
# define printf(x) do {\
		_console_clear((char*)0x800,0x20,120);\
		_console_printchars(0x3f20,(char*)0x800,(x),255);\
	} while(0)
#endif

#ifdef USE_CONSOLE
# include <gigatron/console.h>
# define printf(x) console_print(x,0xffffu)
#endif

#ifdef USE_CPUTS
# include <conio.h>
# define printf(x) cputs(x)
#endif



int main()
{
	printf("Hello world!\n");
	return 0;
}


/***
                           +---------------------------------+
                           |          GLCC-2.2-23            |
                           | -rom=v5a |  -rom=v6 | -rom=dev7 |
+--------------------------+----------+----------+-----------+
| glcc                     |     4063 |     4025 |      3557 |
| --option=CTRL_SIMPLE     |     3874 |     3836 |      3366 |
| \ --option=PRINTF_SIMPLE |     2657 |     2622 |      2269 |
+--------------------------+----------+----------+-----------+
| glcc -Dprintf=cprintf    |     3756 |     3722 |      3250 |
| \ --option=PRINTF_SIMPLE |     2536 |     2498 |      2154 |
+--------------------------+----------+----------+-----------+
| glcc -Dprintf=midcprintf |     2533 |     2498 |      2149 |
| glcc -Dprintf=mincprintf |     1955 |     1917 |      1622 |
+--------------------------+----------+----------+-----------+
| glcc -DUSE_CPUTS         |     1452 |     1452 |      1261 |
+--------------------------+----------+----------+-----------+
| glcc -DUSE_CONSOLE       |     1448 |     1448 |      1256 |
+--------------------------+---------------------+-----------+
| glcc -DUSE_RAWCONSOLE    |      808 |      808 |       695 |
| \ --no-runtime-bss       |      641 |      641 |       539 |
+--------------------------+---------------------+-----------+

                           +---------------------------------+
                           |            GLCC-2.2             |
                           | -rom=v5a |  -rom=v6 | -rom=dev7 |
+--------------------------+----------+----------+-----------+
| glcc                     |     5696 |     5625 |      4915 |
+--------------------------+----------+----------+-----------+
| glcc -Dprintf=cprintf    |     4382 |     4312 |      3800 |
+--------------------------+----------+----------+-----------+
| glcc -Dprintf=mincprintf |     2246 |     2209 |      1888 |
+--------------------------+----------+----------+-----------+
| glcc -DUSE_CONSOLE       |     1736 |     1736 |      1528 |
+--------------------------+---------------------+-----------+
| glcc -DUSE_RAWCONSOLE    |      808 |      808 |       695 |
| \ --no-runtime-bss       |      641 |      641 |       539 |
+--------------------------+---------------------+-----------+

***/