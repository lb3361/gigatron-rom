def scope():

    # LCMPS, LCMPU compare(LAC,[vAC])
    # Trashes T[01]

    avoid_cmpw = (args.cpu <= 4) or ("without_CmpOps" in rominfo)

    def code0():
        nohop()
        if args.cpu >= 6:
            warning("cpu6: use CMPLU/CMPLS instead of _@_lcmps/_@_lcmpu")
            label('__@lcmps_t0t1')
            LDI(T0)
            label('_@_lcmps')
            CMPLS()
            RET()
            label('__@lcmpu_t0t1')
            LDI(T0)
            label('_@_lcmpu')
            CMPLU()
            RET()
        else:
            label('_@_lcmps')
            STW(T3);DEEK();STW(T0)
            LDI(2);ADDW(T3);DEEK();STW(T1)
            label('__@lcmps_t0t1')
            LDW(LAC+2)
            if avoid_cmpw:
                XORW(T1);_BEQ('.lcmp1');_BGE('.lcmp0')
                LDW(LAC+2); _BRA('.lcmp2')
            else:
                _CMPWS(T1);_BEQ('.lcmp1'); RET()
            label('_@_lcmpu')
            STW(T3);DEEK();STW(T0)
            LDI(2);ADDW(T3);DEEK();STW(T1)
            label('__@lcmpu_t0t1')
            LDW(LAC+2)
            if avoid_cmpw:
                XORW(T1);_BEQ('.lcmp1');_BGE('.lcmp0')
                LDW(T1); _BRA('.lcmp2')
                label('.lcmp0')
                LDW(LAC+2); SUBW(T1); RET()
            else:
                _CMPWU(T1);_BEQ('.lcmp1'); RET()
            label('.lcmp1')
            LDW(LAC)
            if avoid_cmpw:
                XORW(T0);_BGE('.lcmp3')
                LDW(T0); label('.lcmp2'); ORI(1); RET()
                label('.lcmp3')
                LDW(LAC); SUBW(T0); RET()
            else:
                _CMPWU(T0);RET()


    module(name='lcmp.s',
           code= [ ('EXPORT', '_@_lcmps'),
                   ('EXPORT', '_@_lcmpu'),
                   ('EXPORT', '__@lcmps_t0t1'),
                   ('EXPORT', '__@lcmpu_t0t1'),
                   ('CODE', '_@_lcmps', code0) ])


    # LCMPX: compare(LAC,[vAC]) for equality only
    def code1():
        nohop()
        label('_@_lcmpx')
        if args.cpu >= 6:
            CMPLS()
            warning("cpu6: use CMPLS instead of _@_lcmpx")
        else:
            STW(T3);DEEK();XORW(LAC);_BNE('.lcmpx1')
            LDI(2);ADDW(T3);DEEK();XORW(LAC+2)
            label('.lcmpx1')
        RET()

    module(name='lcmpx.s',
           code= [ ('EXPORT', '_@_lcmpx'),
                   ('CODE', '_@_lcmpx', code1) ] )

scope()

# Local Variables:
# mode: python
# indent-tabs-mode: ()
# End:
