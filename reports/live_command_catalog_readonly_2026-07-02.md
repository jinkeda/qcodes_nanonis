# Nanonis Live Command Test Report

- Target: `127.0.0.1:6501`
- Config: `E:\Nanonis_Py\qcodes_nanonis\configs\commands`
- Total commands in config: **306**
- Skipped (destructive): **0**
- Tested: **306**
- Successful: **158**
- Failed: **148**

## Breakdown by category

| Category | Count |
|----------|-------|
| PASS | 158 |
| MODULE_UNAVAILABLE | 146 |
| EMPTY_RESPONSE | 1 |
| PROTOCOL_MISMATCH | 0 |
| NANONIS_ERROR | 1 |
| STRUCTURE_MISMATCH | 0 |
| DECODE_ERROR | 0 |
| ENCODE_ERROR | 0 |
| CONNECTION_ERROR | 0 |
| SKIPPED | 0 |

**Likely command-definition bugs (actionable): 0** — none

## Failed commands

| Command | Category | Detail |
|---------|----------|--------|
| `DataLog.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.open: NeedModule_viaHandler.vi:6620030<ERR>\nModule Data Logger not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620030\r\n     ProgrInterf DataLogger Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `PLLFreqSwp.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.open: NeedModule_viaHandler.vi:6620037<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620037\r\n     ProgrInterf FrqSweep Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `Script.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.open: NeedModule_viaHandler.vi:6620022<ERR>\nModule Scripting Tool not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620022\r\n     ProgrInterf Script Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `BeamDefl.HorConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.horconfigget: Module not available' |
| `BeamDefl.IntConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.intconfigget: Module not available' |
| `BeamDefl.VerConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.verconfigget: Module not available' |
| `BiasSpectr.MLSLockinPerSegGet` | NANONIS_ERROR | error status=1, message='Error in command: biasspectr.mlslockinpersegget: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command' |
| `Current.100Get` | MODULE_UNAVAILABLE | error status=1, message='Error in command: current.100get: Cannot access the Current100 module. \nPlease make sure it is running.' |
| `Current.BEEMGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: current.beemget: Cannot access the CurrentBEEM module. \nPlease make sure it is running.' |
| `DataLog.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.chsget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.propsget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.statusget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `FunGen1Ch.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.propsget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen1Ch.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.statusget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen2Ch.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.onoffget: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.propsget: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.SignalGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.signalget: Could not access the selected channel. Check if the index is valid.'; controller emitted 8 extra pre-error byte(s) |
| `FunGen2Ch.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.statusget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen2Ch.WaveformGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.waveformget: Could not access the selected channel. Check if the index is valid.' |
| `GenPICtrl.AOPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.aopropsget: Property Node in ProgrInterf GenericPICtrl AOChProperties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.DemodChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.demodchget: Property Node in ProgrInterf GenericPICtrl DemodSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.ModChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.modchget: Property Node in ProgrInterf GenericPICtrl ModSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.propsget: Property Node in ProgrInterf GenericPICtrl Properties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.AcqChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.acqchsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AcqChannels GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.AutoReverseGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.autoreverseget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AutoReverse Config GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.EndSettlGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.endsettlget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp End Settl GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.NumSweepsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.numsweepsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp NumSweeps GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.ResetSignalsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.resetsignalsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp ResetSignals GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SaveBasenameGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.savebasenameget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveBasename GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SaveDataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.savedataget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveData on-off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SaveOptionsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.saveoptionsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveOptions GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.statusget: Generate User Event in Spec.State.Get.vi->ProgrInterf HS-Swp State Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChBwdDelayGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchbwddelayget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdDelay GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChBwdSwGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchbwdswget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdSweep GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChLimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchlimitsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChNumPtsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchnumptsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Points GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChSigListGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchsiglistget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpStepSignalList Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChSignalGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchsignalget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpSignal GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.SwpChTimingGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.swpchtimingget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Timings GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `HSSwp.ZCtrlOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: hsswp.zctrloffget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp Z-Ctrl Off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `Interf.CtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.ctrlonoffget: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `Interf.CtrlPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.ctrlpropsget: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `Interf.ValGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.valget: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `Interf.WPiezoGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.wpiezoget: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `KelvinCtrl.AmpGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ampget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.BiasLimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.biaslimitsget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.CtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.CtrlSignalGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlsignalget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.gainget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModParamsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modparamsget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.SetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.setpntget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `Laser.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.onoffget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.PowerGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.powerget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.propsget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `MCVA5.ContStateUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContTempUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.CouplingGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.InputModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.UserInGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MProbeBias.CalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index' |
| `MProbeBias.Get` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index' |
| `MProbeBias.RangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index' |
| `MProbeCurrent.CalibrGet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.GainsGet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.Get` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeScanner.ActiveScannerGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.activescannerget: Cannot access the multiprobe switching scanners architecture. \nPlease make sure it is running.' |
| `MProbeScanner.CalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.calibrget: Invalid scanner number' |
| `MProbeScanner.SpeedGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.speedget: Invalid scanner number' |
| `MProbeScanner.XYPosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.xyposget: Invalid scanner number' |
| `MProbeZCtrl.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.gainget: Incorrect Scanner Index' |
| `MProbeZCtrl.HomePropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.homepropsget: Incorrect Scanner Index' |
| `MProbeZCtrl.LimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.limitsget: Incorrect Scanner Index' |
| `MProbeZCtrl.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.onoffget: Incorrect Scanner Index' |
| `MProbeZCtrl.SetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.setpntget: Incorrect Scanner Index' |
| `MProbeZCtrl.ZPosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.zposget: Incorrect Scanner Index' |
| `Motor.PosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: motor.posget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.' |
| `Motor.StepCounterGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: motor.stepcounterget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.' |
| `Osci1T.ChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.chget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.dataget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TimebaseGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.timebaseget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TrigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.trigget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci2T.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.chsget: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.' |
| `Osci2T.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.dataget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.OversamplGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.oversamplget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TimebaseGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.timebaseget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TrigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.trigget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `OsciHR.CalibrModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.calibrmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Scale.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.ChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.chget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.OsciDataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.oscidataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get OSCI Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.OversamplGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.oversamplget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDAvrgCountGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdavrgcountget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDAvrgTypeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdavrgtypeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDDataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psddataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDWeightGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdweightget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDWindowGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdwindowget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PreTrigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.pretrigget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.SamplesGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.samplesget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigArmModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigarmmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigDigChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigdigchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigDigSlopeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigdigslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevHystGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevhystget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevSlopeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevValGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevvalget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `PICtrl.CtrlChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchget: Error trying to access the Generic PI Controller' |
| `PICtrl.CtrlChPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchpropsget: Error trying to access the Generic PI Controller' |
| `PICtrl.InputChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.inputchget: Error trying to access the Generic PI Controller' |
| `PICtrl.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.onoffget: Error trying to access the Generic PI Controller' |
| `PICtrl.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.propsget: Error trying to access the Generic PI Controller' |
| `PLL.AddOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.addonoffget: Module not available' |
| `PLL.AmpCtrlBandwidthGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlbandwidthget: Module not available' |
| `PLL.AmpCtrlGainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlgainget: Module not available' |
| `PLL.AmpCtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlonoffget: Module not available' |
| `PLL.AmpCtrlSetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlsetpntget: Module not available' |
| `PLL.CenterFreqGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.centerfreqget: Module not available' |
| `PLL.ExcRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excrangeget: Module not available' |
| `PLL.ExcitationGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excitationget: Module not available' |
| `PLL.FreqExcOverwriteGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqexcoverwriteget: Feature not available' |
| `PLL.FreqRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqrangeget: Module not available' |
| `PLL.FreqShiftGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftget: Module not available' |
| `PLL.InpCalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inpcalibrget: Module not available' |
| `PLL.InpPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inppropsget: Module not available' |
| `PLL.InpRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inprangeget: Module not available' |
| `PLL.OutOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.outonoffget: Module not available' |
| `PLL.PhasCtrlBandwidthGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlbandwidthget: Module not available' |
| `PLL.PhasCtrlGainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlgainget: Module not available' |
| `PLL.PhasCtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlonoffget: Module not available' |
| `PLLFreqSwp.ParamsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.paramsget: Sweep Module not available' |
| `Script.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.chsget: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.dataget: Cannot access the script module. \nPlease make sure it is running.' |
| `SpectrumAnlzr.ACCouplingGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.accouplingget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.AveragGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.averagget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.BandRMSGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.bandrmsget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.ChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.chget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.CursorPosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.cursorposget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.DCGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.dcget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.dataget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FFTWindowGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.fftwindowget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FreqRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.freqrangeget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FreqResGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.freqresget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `TCPLog.StatusGet` | MODULE_UNAVAILABLE | error status=65536, message='ror in command: tcplog.statusget: Generate User Event in ProgInterf TCPLogger_Status.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TipRec.BufferSizeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tiprec.buffersizeget: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.' |
| `TipRec.DataGet` | EMPTY_RESPONSE | controller returned a successful empty trailer but omitted all declared response fields |
| `TipShaper.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.propsget: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |
| `UserOut.LimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.limitsget: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |

## Per-failure analysis

### `DataLog.Open`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.open: NeedModule_viaHandler.vi:6620030<ERR>\nModule Data Logger not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620030\r\n     ProgrInterf DataLogger Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.Open`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.open: NeedModule_viaHandler.vi:6620037<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620037\r\n     ProgrInterf FrqSweep Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Open`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: script.open: NeedModule_viaHandler.vi:6620022<ERR>\nModule Scripting Tool not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620022\r\n     ProgrInterf Script Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.HorConfigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: beamdefl.horconfigget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.IntConfigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: beamdefl.intconfigget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.VerConfigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: beamdefl.verconfigget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BiasSpectr.MLSLockinPerSegGet`  (NANONIS_ERROR)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: biasspectr.mlslockinpersegget: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Current.100Get`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: current.100get: Cannot access the Current100 module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Current.BEEMGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: current.beemget: Cannot access the CurrentBEEM module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `DataLog.ChsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.chsget: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `DataLog.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 7
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.propsget: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `DataLog.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 7
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.statusget: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen1Ch.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: fungen1ch.propsget: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen1Ch.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: fungen1ch.statusget: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.OnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: fungen2ch.onoffget: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 5
- sent values: `(0,)`
- detail: error status=1, message='Error in command: fungen2ch.propsget: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.SignalGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: fungen2ch.signalget: Could not access the selected channel. Check if the index is valid.'; controller emitted 8 extra pre-error byte(s)
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: fungen2ch.statusget: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.WaveformGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: fungen2ch.waveformget: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenPICtrl.AOPropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 6
- sent values: `()`
- detail: error status=1, message='Error in command: genpictrl.aopropsget: Property Node in ProgrInterf GenericPICtrl AOChProperties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenPICtrl.DemodChGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: genpictrl.demodchget: Property Node in ProgrInterf GenericPICtrl DemodSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenPICtrl.ModChGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: genpictrl.modchget: Property Node in ProgrInterf GenericPICtrl ModSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenPICtrl.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: genpictrl.propsget: Property Node in ProgrInterf GenericPICtrl Properties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.AcqChsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 7
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.acqchsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AcqChannels GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.AutoReverseGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 8
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.autoreverseget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp AutoReverse Config GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.EndSettlGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.endsettlget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp End Settl GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.NumSweepsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.numsweepsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp NumSweeps GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.ResetSignalsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.resetsignalsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp ResetSignals GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SaveBasenameGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.savebasenameget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveBasename GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SaveDataGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.savedataget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveData on-off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SaveOptionsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.saveoptionsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SaveOptions GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.statusget: Generate User Event in Spec.State.Get.vi->ProgrInterf HS-Swp State Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChBwdDelayGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchbwddelayget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdDelay GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChBwdSwGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchbwdswget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh BwdSweep GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChLimitsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchlimitsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChNumPtsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchnumptsget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Points GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChSigListGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 5
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchsiglistget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpStepSignalList Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChSignalGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchsignalget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwpSignal GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.SwpChTimingGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.swpchtimingget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp SwCh Timings GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `HSSwp.ZCtrlOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 5
- sent values: `()`
- detail: error status=1, message='Error in command: hsswp.zctrloffget: Generate User Event in Spec.Parameters.Get.vi->ProgrInterf HS-Swp Z-Ctrl Off GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Interf.CtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: interf.ctrlonoffget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Interf.CtrlPropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: interf.ctrlpropsget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Interf.ValGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: interf.valget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Interf.WPiezoGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: interf.wpiezoget: Cannot access the Interferometer module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.AmpGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.ampget: Could not access controls. Check if the module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.BiasLimitsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.biaslimitsget: Could not access controls. Check if the module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.CtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.ctrlonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.CtrlSignalGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.ctrlsignalget: Could not access controls. Check if the module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.GainGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.gainget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.ModOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.modonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.ModParamsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.modparamsget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.SetpntGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: kelvinctrl.setpntget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Laser.OnOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: laser.onoffget: Cannot access the Laser Control module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Laser.PowerGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: laser.powerget: Cannot access the Laser Control module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Laser.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: laser.propsget: Cannot access the Laser Control module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContStateUpdateGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContTempUpdateGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.CouplingGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.GainGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.InputModeGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.UserInGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.CalibrGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.Get`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.RangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeCurrent.CalibrGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 2
- sent values: `(0, 0)`
- detail: error status=0, message='Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeCurrent.GainsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 8
- sent values: `(0,)`
- detail: error status=0, message='Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeCurrent.Get`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=0, message='Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.ActiveScannerGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: mprobescanner.activescannerget: Cannot access the multiprobe switching scanners architecture. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.CalibrGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 6
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobescanner.calibrget: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.SpeedGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobescanner.speedget: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.XYPosGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobescanner.xyposget: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.GainGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.gainget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.HomePropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.homepropsget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.LimitsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.limitsget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.OnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.onoffget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.SetpntGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.setpntget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.ZPosGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.zposget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Motor.PosGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 3
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: motor.posget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Motor.StepCounterGet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 3
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: motor.stepcounterget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.ChGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: osci1t.chget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.DataGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 4
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci1t.dataget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.TimebaseGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: osci1t.timebaseget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.TrigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: osci1t.trigget: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.ChsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: osci2t.chsget: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.DataGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 6
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci2t.dataget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.OversamplGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: osci2t.oversamplget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.TimebaseGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1, message='Error in command: osci2t.timebaseget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.TrigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 6
- sent values: `()`
- detail: error status=1, message='Error in command: osci2t.trigget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.CalibrModeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.calibrmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Scale.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.ChGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.chget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.OsciDataGet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 5
- sent values: `(0, 0, 0.0)`
- detail: error status=1, message='Error in command: oscihr.oscidataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get OSCI Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.OversamplGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.oversamplget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDAvrgCountGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.psdavrgcountget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDAvrgTypeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.psdavrgtypeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDDataGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 5
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: oscihr.psddataget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD Data.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDWeightGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.psdweightget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDWindowGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.psdwindowget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PreTrigGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.pretrigget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.SamplesGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.samplesget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Measure.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigArmModeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.trigarmmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigDigChGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.trigdigchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigDigSlopeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.trigdigslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevChGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.triglevchget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevHystGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.triglevhystget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevSlopeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.triglevslopeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevValGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.triglevvalget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigModeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.trigmodeget: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Get Triggers.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.CtrlChGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 6
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pictrl.ctrlchget: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.CtrlChPropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pictrl.ctrlchpropsget: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.InputChGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 6
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pictrl.inputchget: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.OnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pictrl.onoffget: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 4
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pictrl.propsget: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AddOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.addonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlBandwidthGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlbandwidthget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlGainGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlgainget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlSetpntGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlsetpntget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.CenterFreqGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.centerfreqget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcRangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.excrangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcitationGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.excitationget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqExcOverwriteGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqexcoverwriteget: Feature not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqRangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqrangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqshiftget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpCalibrGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.inpcalibrget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpPropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.inppropsget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpRangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.inprangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.OutOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.outonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlBandwidthGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.phasctrlbandwidthget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlGainGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.phasctrlgainget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.phasctrlonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.ParamsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.paramsget: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.ChsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: script.chsget: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.DataGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 3
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: script.dataget: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.ACCouplingGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.accouplingget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.AveragGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.averagget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.BandRMSGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.bandrmsget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.ChGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.chget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.CursorPosGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 3
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.cursorposget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.DCGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.dcget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.DataGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 4
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.dataget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FFTWindowGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.fftwindowget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FreqRangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.freqrangeget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FreqResGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.freqresget: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=65536, message='ror in command: tcplog.statusget: Generate User Event in ProgInterf TCPLogger_Status.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipRec.BufferSizeGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: tiprec.buffersizeget: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipRec.DataGet`  (EMPTY_RESPONSE)
- send args: 0, recv args: 5
- sent values: `()`
- detail: controller returned a successful empty trailer but omitted all declared response fields
- likely reason: The controller omitted normal fields without reporting an error. This commonly accompanies a closed/unsupported GUI module; enable the module and retest before changing the schema.

### `TipShaper.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 11
- sent values: `()`
- detail: error status=1, message='Error in command: tipshaper.propsget: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.LimitsGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 2
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: userout.limitsget: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.
