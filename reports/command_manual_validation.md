# Command Manual-Validation Queue

Status: refreshed 2026-07-02 from guarded and unrestricted development runs.

## Validation context

- Protocol source: `TCPProtocol_SPM.pdf`, April 2025, R14718.
- Controller: `127.0.0.1:6501`.
- Controller identity: Nanonis Mimea Software, Generic 5, host/RT release 15632.
- Catalog: 661 commands across 57 modules.
- Full guarded report: `reports/live_command_catalog_readonly_2026-07-02.md`.
- Full development report: `reports/live_command_catalog_full_2026-07-02.md`.
- Focused Lock-In report: `reports/live_command_LockInFreqSwp_2026-07-02.md`.
- Guarded live surface: only `*.Open` and `*Get`; no setters, starts, pulses, moves, sweeps, or quit commands were sent.

## Result summary

- Guarded commands sent: 306.
- Passed: 158.
- Controller/GUI unavailable or invalid selection: 146.
- Required GUI mode: 1 (`BiasSpectr.MLSLockinPerSegGet`).
- Controller returned anomalous empty success: 1 (`TipRec.DataGet`).
- Schema/protocol/encode/decode/structure/connection failures: 0.

The connected release 15632 is newer than the R14718 manual. The unavailable results therefore indicate module/license/selection state rather than a globally outdated controller.

## Unrestricted development result

- Commands sent: 660 of 661; `Util.Quit` was not sent because it terminates the
  Nanonis process and prevents report completion.
- Passed: 324.
- Module/GUI/selection unavailable: 289.
- Valid protocol requests rejected by controller state or synthesized values: 20.
- Long-running/cascaded connection timeouts: 26.
- Empty successful response: 1 (`TipRec.DataGet`).
- Protocol unflatten, encode, decode, and response-structure defects: **0**.

`LockInFreqSwp.Start` initially blocked because the preceding development test
had set the sweep limits to `0–0 Hz` and no sweep signal was selected. After
setting signal index 0, limits `1–10 Hz`, two steps, and short timing, all eight
Lock-In frequency-sweep commands passed. This was invalid controller state, not
a command-schema defect.

`Signals.AddRTSet` also passed its focused retest. Its getter returns signal
display names while its setter takes integer indices; the harness now reuses a
getter value only when both normalized field name and wire type match.

The 26 connection results are dominated by `HSSwp.AcqChsSet` holding the TCP
server, followed by cascaded HSSwp/Interf requests, plus long-running
`HSSwp.Start` and `PLLFreqSwp.Start`. Retest those functions manually with valid
GUI selections, channels, ranges, and short sweep timing. They do not indicate
wire-schema mismatches.

## GUI/controller-dependent commands

### BeamDefl

- `BeamDefl.HorConfigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: beamdefl.horconfigget: Module not available'
- `BeamDefl.IntConfigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: beamdefl.intconfigget: Module not available'
- `BeamDefl.VerConfigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: beamdefl.verconfigget: Module not available'

### BiasSpectr

- `BiasSpectr.MLSLockinPerSegGet` — NANONIS_ERROR: error status=1, message='Error in command: biasspectr.mlslockinpersegget: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command'

### Current

- `Current.100Get` — MODULE_UNAVAILABLE: error status=1, message='Error in command: current.100get: Cannot access the Current100 module. \nPlease make sure it is running.'
- `Current.BEEMGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: current.beemget: Cannot access the CurrentBEEM module. \nPlease make sure it is running.'

### DataLog

- `DataLog.Open` — MODULE_UNAVAILABLE: error status=1, message='Error in command: datalog.open: NeedModule_viaHandler.vi:6620030<ERR>\nModule Data Logger not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620030\r\n     ProgrInterf DataLogger Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- `DataLog.ChsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: datalog.chsget: Cannot access the Data Logger module. \nPlease make sure it is running.'
- `DataLog.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: datalog.propsget: Cannot access the Data Logger module. \nPlease make sure it is running.'
- `DataLog.StatusGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: datalog.statusget: Cannot access the Data Logger module. \nPlease make sure it is running.'

### FunGen1Ch

- `FunGen1Ch.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen1ch.propsget: Could not access controls. Check if the Function Generator is running.'
- `FunGen1Ch.StatusGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen1ch.statusget: Could not access controls. Check if the Function Generator is running.'

### FunGen2Ch

- `FunGen2Ch.OnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen2ch.onoffget: Could not access the selected channel. Check if the index is valid.'
- `FunGen2Ch.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen2ch.propsget: Could not access the selected channel. Check if the index is valid.'
- `FunGen2Ch.SignalGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen2ch.signalget: Could not access the selected channel. Check if the index is valid.'; controller emitted 8 extra pre-error byte(s)
- `FunGen2Ch.StatusGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen2ch.statusget: Could not access controls. Check if the Function Generator is running.'
- `FunGen2Ch.WaveformGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: fungen2ch.waveformget: Could not access the selected channel. Check if the index is valid.'

### GenPICtrl

- `GenPICtrl.AOPropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: genpictrl.aopropsget: Property Node in ProgrInterf GenericPICtrl AOChProperties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `GenPICtrl.DemodChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: genpictrl.demodchget: Property Node in ProgrInterf GenericPICtrl DemodSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `GenPICtrl.ModChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: genpictrl.modchget: Property Node in ProgrInterf GenericPICtrl ModSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `GenPICtrl.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: genpictrl.propsget: Property Node in ProgrInterf GenericPICtrl Properties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'

### HSSwp

- `HSSwp.AcqChsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.acqchsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AcqChannels GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.AutoReverseGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.autoreverseget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AutoReverse Config GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.EndSettlGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.endsettlget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp End Settl GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.NumSweepsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.numsweepsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp NumSweeps GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.ResetSignalsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.resetsignalsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp ResetSignals GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SaveBasenameGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.savebasenameget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveBasename GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SaveDataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.savedataget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveData on-off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SaveOptionsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.saveoptionsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveOptions GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.StatusGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.statusget: Generate User Event in Spec.State.Get.vi->ProgrInterf HS-Swp State Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChBwdDelayGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchbwddelayget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdDelay GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChBwdSwGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchbwdswget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdSweep GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChLimitsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchlimitsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChNumPtsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchnumptsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Points GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChSigListGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchsiglistget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpStepSignalList Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChSignalGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchsignalget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpSignal GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.SwpChTimingGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.swpchtimingget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Timings GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `HSSwp.ZCtrlOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: hsswp.zctrloffget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp Z-Ctrl Off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'

### Interf

- `Interf.CtrlOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: interf.ctrlonoffget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- `Interf.CtrlPropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: interf.ctrlpropsget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- `Interf.ValGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: interf.valget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- `Interf.WPiezoGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: interf.wpiezoget: Cannot access the Interferometer module. \nPlease make sure it is running.'

### KelvinCtrl

- `KelvinCtrl.AmpGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.ampget: Could not access controls. Check if the module is running.'
- `KelvinCtrl.BiasLimitsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.biaslimitsget: Could not access controls. Check if the module is running.'
- `KelvinCtrl.CtrlOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.ctrlonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- `KelvinCtrl.CtrlSignalGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.ctrlsignalget: Could not access controls. Check if the module is running.'
- `KelvinCtrl.GainGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.gainget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- `KelvinCtrl.ModOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.modonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- `KelvinCtrl.ModParamsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.modparamsget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- `KelvinCtrl.SetpntGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: kelvinctrl.setpntget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'

### Laser

- `Laser.OnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: laser.onoffget: Cannot access the Laser Control module. \nPlease make sure it is running.'
- `Laser.PowerGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: laser.powerget: Cannot access the Laser Control module. \nPlease make sure it is running.'
- `Laser.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: laser.propsget: Cannot access the Laser Control module. \nPlease make sure it is running.'

### MCVA5

- `MCVA5.ContStateUpdateGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- `MCVA5.ContTempUpdateGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- `MCVA5.CouplingGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- `MCVA5.GainGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- `MCVA5.InputModeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- `MCVA5.UserInGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.'

### MProbeBias

- `MProbeBias.CalibrGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index'
- `MProbeBias.Get` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index'
- `MProbeBias.RangeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index'

### MProbeCurrent

- `MProbeCurrent.CalibrGet` — MODULE_UNAVAILABLE: error status=0, message='Incorrect Scanner Index'
- `MProbeCurrent.GainsGet` — MODULE_UNAVAILABLE: error status=0, message='Incorrect Scanner Index'
- `MProbeCurrent.Get` — MODULE_UNAVAILABLE: error status=0, message='Incorrect Scanner Index'

### MProbeScanner

- `MProbeScanner.ActiveScannerGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobescanner.activescannerget: Cannot access the multiprobe switching scanners architecture. \nPlease make sure it is running.'
- `MProbeScanner.CalibrGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobescanner.calibrget: Invalid scanner number'
- `MProbeScanner.SpeedGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobescanner.speedget: Invalid scanner number'
- `MProbeScanner.XYPosGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobescanner.xyposget: Invalid scanner number'

### MProbeZCtrl

- `MProbeZCtrl.GainGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.gainget: Incorrect Scanner Index'
- `MProbeZCtrl.HomePropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.homepropsget: Incorrect Scanner Index'
- `MProbeZCtrl.LimitsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.limitsget: Incorrect Scanner Index'
- `MProbeZCtrl.OnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.onoffget: Incorrect Scanner Index'
- `MProbeZCtrl.SetpntGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.setpntget: Incorrect Scanner Index'
- `MProbeZCtrl.ZPosGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: mprobezctrl.zposget: Incorrect Scanner Index'

### Motor

- `Motor.PosGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: motor.posget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.'
- `Motor.StepCounterGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: motor.stepcounterget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.'

### Osci1T

- `Osci1T.ChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci1t.chget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- `Osci1T.DataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci1t.dataget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- `Osci1T.TimebaseGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci1t.timebaseget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- `Osci1T.TrigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci1t.trigget: Cannot access the Oscilloscope. \nPlease make sure it is running.'

### Osci2T

- `Osci2T.ChsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci2t.chsget: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.'
- `Osci2T.DataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci2t.dataget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- `Osci2T.OversamplGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci2t.oversamplget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- `Osci2T.TimebaseGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci2t.timebaseget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- `Osci2T.TrigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: osci2t.trigget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'

### OsciHR

- `OsciHR.CalibrModeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.calibrmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Scale.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.ChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.chget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.OsciDataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.oscidataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get OSCI Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.OversamplGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.oversamplget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PSDAvrgCountGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.psdavrgcountget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PSDAvrgTypeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.psdavrgtypeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PSDDataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.psddataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PSDWeightGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.psdweightget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PSDWindowGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.psdwindowget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.PreTrigGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.pretrigget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.SamplesGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.samplesget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigArmModeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.trigarmmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigDigChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.trigdigchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigDigSlopeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.trigdigslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigLevChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.triglevchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigLevHystGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.triglevhystget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigLevSlopeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.triglevslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigLevValGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.triglevvalget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- `OsciHR.TrigModeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: oscihr.trigmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'

### PICtrl

- `PICtrl.CtrlChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pictrl.ctrlchget: Error trying to access the Generic PI Controller'
- `PICtrl.CtrlChPropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pictrl.ctrlchpropsget: Error trying to access the Generic PI Controller'
- `PICtrl.InputChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pictrl.inputchget: Error trying to access the Generic PI Controller'
- `PICtrl.OnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pictrl.onoffget: Error trying to access the Generic PI Controller'
- `PICtrl.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pictrl.propsget: Error trying to access the Generic PI Controller'

### PLL

- `PLL.AddOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.addonoffget: Module not available'
- `PLL.AmpCtrlBandwidthGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.ampctrlbandwidthget: Module not available'
- `PLL.AmpCtrlGainGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.ampctrlgainget: Module not available'
- `PLL.AmpCtrlOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.ampctrlonoffget: Module not available'
- `PLL.AmpCtrlSetpntGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.ampctrlsetpntget: Module not available'
- `PLL.CenterFreqGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.centerfreqget: Module not available'
- `PLL.ExcRangeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.excrangeget: Module not available'
- `PLL.ExcitationGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.excitationget: Module not available'
- `PLL.FreqExcOverwriteGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.freqexcoverwriteget: Feature not available'
- `PLL.FreqRangeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.freqrangeget: Module not available'
- `PLL.FreqShiftGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.freqshiftget: Module not available'
- `PLL.InpCalibrGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.inpcalibrget: Module not available'
- `PLL.InpPropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.inppropsget: Module not available'
- `PLL.InpRangeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.inprangeget: Module not available'
- `PLL.OutOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.outonoffget: Module not available'
- `PLL.PhasCtrlBandwidthGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.phasctrlbandwidthget: Module not available'
- `PLL.PhasCtrlGainGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.phasctrlgainget: Module not available'
- `PLL.PhasCtrlOnOffGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pll.phasctrlonoffget: Module not available'

### PLLFreqSwp

- `PLLFreqSwp.Open` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pllfreqswp.open: NeedModule_viaHandler.vi:6620037<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620037\r\n     ProgrInterf FrqSweep Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- `PLLFreqSwp.ParamsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: pllfreqswp.paramsget: Sweep Module not available'

### Script

- `Script.Open` — MODULE_UNAVAILABLE: error status=1, message='Error in command: script.open: NeedModule_viaHandler.vi:6620022<ERR>\nModule Scripting Tool not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620022\r\n     ProgrInterf Script Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- `Script.ChsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: script.chsget: Cannot access the script module. \nPlease make sure it is running.'
- `Script.DataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: script.dataget: Cannot access the script module. \nPlease make sure it is running.'

### SpectrumAnlzr

- `SpectrumAnlzr.ACCouplingGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.accouplingget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.AveragGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.averagget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.BandRMSGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.bandrmsget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.ChGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.chget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.CursorPosGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.cursorposget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.DCGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.dcget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.DataGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.dataget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.FFTWindowGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.fftwindowget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.FreqRangeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.freqrangeget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- `SpectrumAnlzr.FreqResGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: spectrumanlzr.freqresget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'

### TCPLog

- `TCPLog.StatusGet` — MODULE_UNAVAILABLE: error status=65536, message='ror in command: tcplog.statusget: Generate User Event in ProgInterf TCPLogger_Status.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'

### TipRec

- `TipRec.BufferSizeGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: tiprec.buffersizeget: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.'
- `TipRec.DataGet` — EMPTY_RESPONSE: controller returned a successful empty trailer but omitted all declared response fields

### TipShaper

- `TipShaper.PropsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: tipshaper.propsget: Cannot access the Tip Shaper module. \nPlease make sure it is running.'

### UserOut

- `UserOut.LimitsGet` — MODULE_UNAVAILABLE: error status=1, message='Error in command: userout.limitsget: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'

## State-changing or argument-dependent commands not sent automatically

These 355 definitions pass the manual/static schema audit but require operator-approved values and hardware state. Test them manually or through a workflow with snapshot/restore and safety preflight.

- **AtomTrack** (4): `AtomTrack.CtrlSet`, `AtomTrack.DriftComp`, `AtomTrack.PropsSet`, `AtomTrack.QuickCompStart`
- **AutoApproach** (1): `AutoApproach.OnOffSet`
- **BeamDefl** (4): `BeamDefl.AutoOffset`, `BeamDefl.HorConfigSet`, `BeamDefl.IntConfigSet`, `BeamDefl.VerConfigSet`
- **Bias** (4): `Bias.CalibrSet`, `Bias.Pulse`, `Bias.RangeSet`, `Bias.Set`
- **BiasSpectr** (17): `BiasSpectr.AdvPropsSet`, `BiasSpectr.AltZCtrlSet`, `BiasSpectr.ChsSet`, `BiasSpectr.DigSyncSet`, `BiasSpectr.LimitsSet`, `BiasSpectr.MLSLockinPerSegSet`, `BiasSpectr.MLSModeSet`, `BiasSpectr.MLSValsSet`, `BiasSpectr.PropsSet`, `BiasSpectr.PulseSeqSyncSet`, `BiasSpectr.SafeCond1Set`, `BiasSpectr.SafeCond2Set`, `BiasSpectr.Start`, `BiasSpectr.Stop`, `BiasSpectr.TTLSyncSet`, `BiasSpectr.TimingSet`, `BiasSpectr.ZOffRevertSet`
- **BiasSwp** (3): `BiasSwp.LimitsSet`, `BiasSwp.PropsSet`, `BiasSwp.Start`
- **CPDComp** (2): `CPDComp.Close`, `CPDComp.ParamsSet`
- **Current** (2): `Current.CalibrSet`, `Current.GainSet`
- **DataLog** (4): `DataLog.ChsSet`, `DataLog.PropsSet`, `DataLog.Start`, `DataLog.Stop`
- **DigLines** (3): `DigLines.OutStatusSet`, `DigLines.PropsSet`, `DigLines.Pulse`
- **File** (1): `File.datLoad`
- **FolMe** (7): `FolMe.OversamplSet`, `FolMe.PSExpSet`, `FolMe.PSOnOffSet`, `FolMe.PSPropsSet`, `FolMe.SpeedSet`, `FolMe.Stop`, `FolMe.XYPosSet`
- **FunGen1Ch** (4): `FunGen1Ch.IdleSet`, `FunGen1Ch.PropsSet`, `FunGen1Ch.Start`, `FunGen1Ch.Stop`
- **FunGen2Ch** (7): `FunGen2Ch.IdleSet`, `FunGen2Ch.OnOffSet`, `FunGen2Ch.PropsSet`, `FunGen2Ch.SignalSet`, `FunGen2Ch.Start`, `FunGen2Ch.Stop`, `FunGen2Ch.WaveformSet`
- **GenPICtrl** (6): `GenPICtrl.AOPropsSet`, `GenPICtrl.AOValSet`, `GenPICtrl.DemodChSet`, `GenPICtrl.ModChSet`, `GenPICtrl.OnOffSet`, `GenPICtrl.PropsSet`
- **GenSwp** (6): `GenSwp.AcqChsSet`, `GenSwp.LimitsSet`, `GenSwp.PropsSet`, `GenSwp.Start`, `GenSwp.Stop`, `GenSwp.SwpSignalSet`
- **HSSwp** (17): `HSSwp.AcqChsSet`, `HSSwp.AutoReverseSet`, `HSSwp.EndSettlSet`, `HSSwp.NumSweepsSet`, `HSSwp.ResetSignalsSet`, `HSSwp.SaveBasenameSet`, `HSSwp.SaveDataSet`, `HSSwp.SaveOptionsSet`, `HSSwp.Start`, `HSSwp.Stop`, `HSSwp.SwpChBwdDelaySet`, `HSSwp.SwpChBwdSwSet`, `HSSwp.SwpChLimitsSet`, `HSSwp.SwpChNumPtsSet`, `HSSwp.SwpChSignalSet`, `HSSwp.SwpChTimingSet`, `HSSwp.ZCtrlOffSet`
- **Interf** (6): `Interf.CtrlCalibrOpen`, `Interf.CtrlNullDefl`, `Interf.CtrlOnOffSet`, `Interf.CtrlPropsSet`, `Interf.CtrlReset`, `Interf.WPiezoSet`
- **KelvinCtrl** (7): `KelvinCtrl.BiasLimitsSet`, `KelvinCtrl.CtrlOnOffSet`, `KelvinCtrl.CtrlSignalSet`, `KelvinCtrl.GainSet`, `KelvinCtrl.ModOnOffSet`, `KelvinCtrl.ModParamsSet`, `KelvinCtrl.SetpntSet`
- **Laser** (2): `Laser.OnOffSet`, `Laser.PropsSet`
- **LockIn** (15): `LockIn.DemodHPFilterSet`, `LockIn.DemodHarmonicSet`, `LockIn.DemodLPFilterSet`, `LockIn.DemodPhasRegSet`, `LockIn.DemodPhasSet`, `LockIn.DemodRTSignalsSet`, `LockIn.DemodSignalSet`, `LockIn.DemodSyncFilterSet`, `LockIn.ModAmpSet`, `LockIn.ModHarmonicSet`, `LockIn.ModOnOffSet`, `LockIn.ModPhasFreqSet`, `LockIn.ModPhasRegSet`, `LockIn.ModPhasSet`, `LockIn.ModSignalSet`
- **LockInFreqSwp** (4): `LockInFreqSwp.LimitsSet`, `LockInFreqSwp.PropsSet`, `LockInFreqSwp.SignalSet`, `LockInFreqSwp.Start`
- **MCVA5** (8): `MCVA5.ContStateUpdateSet`, `MCVA5.ContTempUpdateSet`, `MCVA5.CouplingSet`, `MCVA5.GainSet`, `MCVA5.InputModeSet`, `MCVA5.SingleStateUpdate`, `MCVA5.SingleTempUpdate`, `MCVA5.UserInSet`
- **MPass** (3): `MPass.Activate`, `MPass.Load`, `MPass.Save`
- **MProbeBias** (4): `MProbeBias.CalibrSet`, `MProbeBias.Pulse`, `MProbeBias.RangeSet`, `MProbeBias.Set`
- **MProbeCurrent** (2): `MProbeCurrent.CalibrSet`, `MProbeCurrent.GainSet`
- **MProbeScanner** (5): `MProbeScanner.CalibrSet`, `MProbeScanner.ScannerSwitch`, `MProbeScanner.SpeedSet`, `MProbeScanner.Stop`, `MProbeScanner.XYPosSet`
- **MProbeZCtrl** (8): `MProbeZCtrl.GainSet`, `MProbeZCtrl.Home`, `MProbeZCtrl.HomePropsSet`, `MProbeZCtrl.LimitsSet`, `MProbeZCtrl.OnOffSet`, `MProbeZCtrl.SetpntSet`, `MProbeZCtrl.Withdraw`, `MProbeZCtrl.ZPosSet`
- **Marks** (8): `Marks.LineDraw`, `Marks.LinesDraw`, `Marks.LinesErase`, `Marks.LinesVisibleSet`, `Marks.PointDraw`, `Marks.PointsDraw`, `Marks.PointsErase`, `Marks.PointsVisibleSet`
- **Motor** (4): `Motor.FreqAmpSet`, `Motor.StartClosedLoop`, `Motor.StartMove`, `Motor.StopMove`
- **OCSync** (2): `OCSync.AnglesSet`, `OCSync.LinkAnglesSet`
- **Osci1T** (4): `Osci1T.ChSet`, `Osci1T.Run`, `Osci1T.TimebaseSet`, `Osci1T.TrigSet`
- **Osci2T** (5): `Osci2T.ChsSet`, `Osci2T.OversamplSet`, `Osci2T.Run`, `Osci2T.TimebaseSet`, `Osci2T.TrigSet`
- **OsciHR** (21): `OsciHR.CalibrModeSet`, `OsciHR.ChSet`, `OsciHR.OversamplSet`, `OsciHR.PSDAvrgCountSet`, `OsciHR.PSDAvrgRestart`, `OsciHR.PSDAvrgTypeSet`, `OsciHR.PSDShow`, `OsciHR.PSDWeightSet`, `OsciHR.PSDWindowSet`, `OsciHR.PreTrigSet`, `OsciHR.Run`, `OsciHR.SamplesSet`, `OsciHR.TrigArmModeSet`, `OsciHR.TrigDigChSet`, `OsciHR.TrigDigSlopeSet`, `OsciHR.TrigLevChSet`, `OsciHR.TrigLevHystSet`, `OsciHR.TrigLevSlopeSet`, `OsciHR.TrigLevValSet`, `OsciHR.TrigModeSet`, `OsciHR.TrigRearm`
- **PICtrl** (5): `PICtrl.CtrlChPropsSet`, `PICtrl.CtrlChSet`, `PICtrl.InputChSet`, `PICtrl.OnOffSet`, `PICtrl.PropsSet`
- **PLL** (25): `PLL.AddOnOffSet`, `PLL.AmpCtrlBandwidthSet`, `PLL.AmpCtrlGainSet`, `PLL.AmpCtrlOnOffSet`, `PLL.AmpCtrlSetpntSet`, `PLL.CenterFreqSet`, `PLL.DemodFilterSet`, `PLL.DemodHarmonicSet`, `PLL.DemodInputSet`, `PLL.DemodPhasRefSet`, `PLL.ExcRangeSet`, `PLL.ExcitationSet`, `PLL.FreqExcOverwriteSet`, `PLL.FreqRangeSet`, `PLL.FreqShiftAutoCenter`, `PLL.FreqShiftSet`, `PLL.InpCalibrSet`, `PLL.InpPropsSet`, `PLL.InpRangeSet`, `PLL.OutOnOffSet`, `PLL.PerfectPLLApply`, `PLL.PerfectPLLUpdtZTC`, `PLL.PhasCtrlBandwidthSet`, `PLL.PhasCtrlGainSet`, `PLL.PhasCtrlOnOffSet`
- **PLLFreqSwp** (3): `PLLFreqSwp.ParamsSet`, `PLLFreqSwp.Start`, `PLLFreqSwp.Stop`
- **PLLPhasSwp** (2): `PLLPhasSwp.Start`, `PLLPhasSwp.Stop`
- **PLLQCtrl** (4): `PLLQCtrl.AccessRequest`, `PLLQCtrl.OnOffSet`, `PLLQCtrl.PhaseSet`, `PLLQCtrl.QGainSet`
- **PLLSignalAnlzr** (7): `PLLSignalAnlzr.ChSet`, `PLLSignalAnlzr.FFTAvgRestart`, `PLLSignalAnlzr.FFTPropsSet`, `PLLSignalAnlzr.TimebaseSet`, `PLLSignalAnlzr.TrigAuto`, `PLLSignalAnlzr.TrigRearm`, `PLLSignalAnlzr.TrigSet`
- **PLLZoomFFT** (3): `PLLZoomFFT.AvgRestart`, `PLLZoomFFT.ChSet`, `PLLZoomFFT.PropsSet`
- **Pattern** (8): `Pattern.CloudSet`, `Pattern.ExpOpen`, `Pattern.ExpPause`, `Pattern.ExpStart`, `Pattern.ExpStop`, `Pattern.GridSet`, `Pattern.LineSet`, `Pattern.PropsSet`
- **Piezo** (9): `Piezo.DriftCompSet`, `Piezo.HystFileLoad`, `Piezo.HystFileSave`, `Piezo.HystOnOffSet`, `Piezo.HystValsSet`, `Piezo.RangeSet`, `Piezo.SensSet`, `Piezo.TiltSet`, `Piezo.XYZLimitsSet`
- **SafeTip** (2): `SafeTip.OnOffSet`, `SafeTip.PropsSet`
- **Scan** (11): `Scan.Action`, `Scan.BackgroundDelete`, `Scan.BackgroundPaste`, `Scan.BufferSet`, `Scan.FrameDataGrab`, `Scan.FrameSet`, `Scan.PropsSet`, `Scan.Save`, `Scan.SpeedSet`, `Scan.WaitEndOfLine`, `Scan.WaitEndOfScan`
- **Script** (12): `Script.Autosave`, `Script.ChsSet`, `Script.Deploy`, `Script.LUTDeploy`, `Script.LUTLoad`, `Script.LUTOpen`, `Script.LUTSave`, `Script.Load`, `Script.Run`, `Script.Save`, `Script.Stop`, `Script.Undeploy`
- **SignalChart** (1): `SignalChart.ChsSet`
- **Signals** (1): `Signals.AddRTSet`
- **SpectrumAnlzr** (8): `SpectrumAnlzr.ACCouplingSet`, `SpectrumAnlzr.AveragSet`, `SpectrumAnlzr.ChSet`, `SpectrumAnlzr.CursorPosSet`, `SpectrumAnlzr.FFTWindowSet`, `SpectrumAnlzr.FreqRangeSet`, `SpectrumAnlzr.FreqResSet`, `SpectrumAnlzr.Run`
- **TCPLog** (4): `TCPLog.ChsSet`, `TCPLog.OversamplSet`, `TCPLog.Start`, `TCPLog.Stop`
- **TipRec** (3): `TipRec.BufferClear`, `TipRec.BufferSizeSet`, `TipRec.DataSave`
- **TipShaper** (2): `TipShaper.PropsSet`, `TipShaper.Start`
- **UserIn** (1): `UserIn.CalibrSet`
- **UserOut** (7): `UserOut.CalcSignalConfigSet`, `UserOut.CalcSignalNameSet`, `UserOut.CalibrSet`, `UserOut.LimitsSet`, `UserOut.ModeSet`, `UserOut.MonitorChSet`, `UserOut.ValSet`
- **Util** (11): `Util.AcqPeriodSet`, `Util.LayoutLoad`, `Util.LayoutSave`, `Util.Lock`, `Util.Quit`, `Util.RTFreqSet`, `Util.RTOversamplSet`, `Util.SessionPathSet`, `Util.SettingsLoad`, `Util.SettingsSave`, `Util.UnLock`
- **ZCtrl** (13): `ZCtrl.ActiveCtrlSet`, `ZCtrl.GainSet`, `ZCtrl.Home`, `ZCtrl.HomePropsSet`, `ZCtrl.LimitsEnabledSet`, `ZCtrl.LimitsSet`, `ZCtrl.OnOffSet`, `ZCtrl.SetpntSet`, `ZCtrl.SwitchOffDelaySet`, `ZCtrl.TipLiftSet`, `ZCtrl.Withdraw`, `ZCtrl.WithdrawRateSet`, `ZCtrl.ZPosSet`
- **ZSpectr** (13): `ZSpectr.AdvPropsSet`, `ZSpectr.ChsSet`, `ZSpectr.DigSyncSet`, `ZSpectr.PropsSet`, `ZSpectr.PulseSeqSyncSet`, `ZSpectr.RangeSet`, `ZSpectr.Retract2ndSet`, `ZSpectr.RetractDelaySet`, `ZSpectr.RetractSet`, `ZSpectr.Start`, `ZSpectr.Stop`, `ZSpectr.TTLSyncSet`, `ZSpectr.TimingSet`
