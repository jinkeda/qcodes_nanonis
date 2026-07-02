# Nanonis Live Command Test Report

- Target: `127.0.0.1:6501`
- Config: `E:\Nanonis_Py\qcodes_nanonis\configs\commands`
- Total commands in config: **661**
- Skipped (destructive): **1** (`Util.Quit`)
- Tested: **660**
- Successful: **324**
- Failed: **336**
- Consolidation: `Signals.AddRTSet` and `LockInFreqSwp.Start` passed focused
  retests after correcting harness argument reuse and assigning valid Lock-In
  sweep prerequisites. See `live_command_LockInFreqSwp_2026-07-02.md`.

## Breakdown by category

| Category | Count |
|----------|-------|
| PASS | 324 |
| MODULE_UNAVAILABLE | 289 |
| EMPTY_RESPONSE | 1 |
| PROTOCOL_MISMATCH | 0 |
| NANONIS_ERROR | 20 |
| STRUCTURE_MISMATCH | 0 |
| DECODE_ERROR | 0 |
| ENCODE_ERROR | 0 |
| CONNECTION_ERROR | 26 |
| SKIPPED | 1 |

**Likely command-definition bugs (actionable): 0** — none

## Failed commands

| Command | Category | Detail |
|---------|----------|--------|
| `BeamDefl.HorConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.horconfigget: Module not available' |
| `BeamDefl.IntConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.intconfigget: Module not available' |
| `BeamDefl.VerConfigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.verconfigget: Module not available' |
| `BeamDefl.HorConfigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.horconfigset: Module not available' |
| `BeamDefl.IntConfigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.intconfigset: Module not available' |
| `BeamDefl.VerConfigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.verconfigset: Module not available' |
| `BeamDefl.AutoOffset` | MODULE_UNAVAILABLE | error status=1, message='Error in command: beamdefl.autooffset: Module not available' |
| `BiasSpectr.MLSLockinPerSegGet` | NANONIS_ERROR | error status=1, message='Error in command: biasspectr.mlslockinpersegget: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command' |
| `BiasSpectr.MLSLockinPerSegSet` | NANONIS_ERROR | error status=1, message='Error in command: biasspectr.mlslockinpersegset: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command' |
| `BiasSpectr.MLSValsSet` | NANONIS_ERROR | error status=1, message='Error in command: biasspectr.mlsvalsset: Bias spectroscopy module is not in multi segment mode.  This must be explicitly set before calling this command' |
| `Current.100Get` | MODULE_UNAVAILABLE | error status=1, message='Error in command: current.100get: Cannot access the Current100 module. \nPlease make sure it is running.' |
| `Current.BEEMGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: current.beemget: Cannot access the CurrentBEEM module. \nPlease make sure it is running.' |
| `DataLog.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.open: NeedModule_viaHandler.vi:6620030<ERR>\nModule Data Logger not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620030\r\n     ProgrInterf DataLogger Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `DataLog.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.chsget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.propsget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.statusget: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.ChsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.chsset: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.propsset: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `DataLog.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.stop: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `FunGen1Ch.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.propsget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen1Ch.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.statusget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen1Ch.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.propsset: Could not access controls. Check if the Function Generator is running.' |
| `FunGen1Ch.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.stop: Could not access controls. Check if the Function Generator is running.' |
| `FunGen2Ch.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.onoffget: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.propsget: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.SignalGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.signalget: Could not access the selected channel. Check if the index is valid.'; controller emitted 8 extra pre-error byte(s) |
| `FunGen2Ch.StatusGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.statusget: Could not access controls. Check if the Function Generator is running.' |
| `FunGen2Ch.WaveformGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.waveformget: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.OnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.onoffset: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.propsset: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.SignalSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.signalset: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.WaveformSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.waveformset: Could not access the selected channel. Check if the index is valid.' |
| `FunGen2Ch.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.stop: Could not access controls. Check if the Function Generator is running.' |
| `GenPICtrl.AOPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.aopropsget: Property Node in ProgrInterf GenericPICtrl AOChProperties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.DemodChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.demodchget: Property Node in ProgrInterf GenericPICtrl DemodSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.ModChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.modchget: Property Node in ProgrInterf GenericPICtrl ModSignal Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.propsget: Property Node in ProgrInterf GenericPICtrl Properties Get.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.AOPropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: genpictrl.aopropsset: Property Node in ProgrInterf GenericPICtrl AOChProperties Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.DemodChSet` | NANONIS_ERROR | error status=1, message='Error in command: genpictrl.demodchset: Enqueue Element in ProgrInterf GenericPICtrl DemodSignal Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.ModChSet` | NANONIS_ERROR | error status=1, message='Error in command: genpictrl.modchset: Enqueue Element in ProgrInterf GenericPICtrl ModSignal Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.OnOffSet` | NANONIS_ERROR | error status=1, message='Error in command: genpictrl.onoffset: Enqueue Element in ProgrInterf GenericPICtrl Status Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `GenPICtrl.PropsSet` | NANONIS_ERROR | error status=1, message='Error in command: genpictrl.propsset: Enqueue Element in ProgrInterf GenericPICtrl Properties Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
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
| `HSSwp.AcqChsSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.AutoReverseSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.EndSettlSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.NumSweepsSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.ResetSignalsSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.SaveBasenameSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.SaveDataSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.SaveOptionsSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.SwpChBwdDelaySet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.SwpChBwdSwSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.SwpChLimitsSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.SwpChNumPtsSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.SwpChSignalSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.SwpChTimingSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `HSSwp.ZCtrlOffSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `HSSwp.Stop` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `Interf.CtrlOnOffGet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `Interf.CtrlPropsGet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `Interf.ValGet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `Interf.WPiezoGet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `Interf.CtrlOnOffSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `Interf.CtrlPropsSet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `Interf.WPiezoSet` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `Interf.CtrlCalibrOpen` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `Interf.CtrlNullDefl` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.ctrlnulldefl: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `Interf.CtrlReset` | MODULE_UNAVAILABLE | error status=1, message='Error in command: interf.ctrlreset: Cannot access the Interferometer module. \nPlease make sure it is running.' |
| `KelvinCtrl.AmpGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ampget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.BiasLimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.biaslimitsget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.CtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.CtrlSignalGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlsignalget: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.gainget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modonoffget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModParamsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modparamsget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.SetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.setpntget: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.BiasLimitsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.biaslimitsset: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.CtrlOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlonoffset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.CtrlSignalSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.ctrlsignalset: Could not access controls. Check if the module is running.' |
| `KelvinCtrl.GainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.gainset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modonoffset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.ModParamsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.modparamsset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `KelvinCtrl.SetpntSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: kelvinctrl.setpntset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.' |
| `Laser.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.onoffget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.PowerGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.powerget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.propsget: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.OnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.onoffset: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `Laser.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: laser.propsset: Cannot access the Laser Control module. \nPlease make sure it is running.' |
| `MCVA5.ContStateUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContTempUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.CouplingGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.InputModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.UserInGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContStateUpdateSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.contstateupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContTempUpdateSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.conttempupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.CouplingSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.couplingset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.GainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.gainset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.InputModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.inputmodeset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.UserInSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.userinset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.SingleStateUpdate` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.singlestateupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.SingleTempUpdate` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.singletempupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MProbeBias.CalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index' |
| `MProbeBias.Get` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index' |
| `MProbeBias.RangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index' |
| `MProbeBias.CalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.calibrset: Incorrect Scanner Index' |
| `MProbeBias.RangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.rangeset: Incorrect Scanner Index' |
| `MProbeBias.Set` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.set: Incorrect Scanner Index' |
| `MProbeBias.Pulse` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.pulse: Incorrect Scanner Index' |
| `MProbeCurrent.CalibrGet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.GainsGet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.Get` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.CalibrSet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeCurrent.GainSet` | MODULE_UNAVAILABLE | error status=0, message='Incorrect Scanner Index' |
| `MProbeScanner.ActiveScannerGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.activescannerget: Cannot access the multiprobe switching scanners architecture. \nPlease make sure it is running.' |
| `MProbeScanner.CalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.calibrget: Invalid scanner number' |
| `MProbeScanner.SpeedGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.speedget: Invalid scanner number' |
| `MProbeScanner.XYPosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.xyposget: Invalid scanner number' |
| `MProbeScanner.CalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.calibrset: Invalid scanner number' |
| `MProbeScanner.SpeedSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.speedset: Invalid scanner number' |
| `MProbeScanner.XYPosSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.xyposset: Invalid scanner number' |
| `MProbeScanner.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.stop: Invalid scanner number' |
| `MProbeScanner.ScannerSwitch` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobescanner.scannerswitch: Invalid scanner number' |
| `MProbeZCtrl.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.gainget: Incorrect Scanner Index' |
| `MProbeZCtrl.HomePropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.homepropsget: Incorrect Scanner Index' |
| `MProbeZCtrl.LimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.limitsget: Incorrect Scanner Index' |
| `MProbeZCtrl.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.onoffget: Incorrect Scanner Index' |
| `MProbeZCtrl.SetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.setpntget: Incorrect Scanner Index' |
| `MProbeZCtrl.ZPosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.zposget: Incorrect Scanner Index' |
| `MProbeZCtrl.GainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.gainset: Incorrect Scanner Index' |
| `MProbeZCtrl.HomePropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.homepropsset: Incorrect Scanner Index' |
| `MProbeZCtrl.LimitsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.limitsset: Incorrect Scanner Index' |
| `MProbeZCtrl.OnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.onoffset: Incorrect Scanner Index' |
| `MProbeZCtrl.SetpntSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.setpntset: Incorrect Scanner Index' |
| `MProbeZCtrl.ZPosSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.zposset: Incorrect Scanner Index' |
| `MProbeZCtrl.Home` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.home: Incorrect Scanner Index' |
| `MProbeZCtrl.Withdraw` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobezctrl.withdraw: Incorrect Scanner Index' |
| `Motor.PosGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: motor.posget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.' |
| `Motor.StepCounterGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: motor.stepcounterget: Cannot access "Motor Control" Module.\nPlease make sure it is running.\rElse, this Function may not be supported by this Motor Control Module.' |
| `Osci1T.ChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.chget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.dataget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TimebaseGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.timebaseget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TrigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.trigget: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.ChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.chset: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TimebaseSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.timebaseset: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci1T.TrigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci1t.trigset: Cannot access the Oscilloscope. \nPlease make sure it is running.' |
| `Osci2T.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.chsget: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.' |
| `Osci2T.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.dataget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.OversamplGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.oversamplget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TimebaseGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.timebaseget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TrigGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.trigget: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.ChsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.chsset: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.' |
| `Osci2T.OversamplSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.oversamplset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TimebaseSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.timebaseset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
| `Osci2T.TrigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: osci2t.trigset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.' |
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
| `OsciHR.CalibrModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.calibrmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Calibration mode.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.ChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.chset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Channel v3.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.OversamplSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.oversamplset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Oversampling.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDAvrgCountSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdavrgcountset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Count.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDAvrgTypeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdavrgtypeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Averaging.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDWeightSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdweightset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Weighting.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDWindowSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdwindowset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Window.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PreTrigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.pretrigset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Pretrigger.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.SamplesSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.samplesset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Samples.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigArmModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigarmmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Mode.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigDigChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigdigchset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Digital Trigger Channel.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigDigSlopeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigdigslopeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Digital Trigger Polarity.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevchset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set LEvel Trigger Channel v3.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevHystSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevhystset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Hysteresis.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevSlopeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevslopeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Polarity.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigLevValSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.triglevvalset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Level.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.TrigModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Type.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDAvrgRestart` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdavrgrestart: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Restart.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.PSDShow` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.psdshow: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Show PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `OsciHR.Run` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.run: NeedModule_viaHandler.vi:6620033<ERR>\nModule Oscilloscope - High-Resolution not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620033\r\n     ProgrInterf Osci FPGA Run.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `OsciHR.TrigRearm` | MODULE_UNAVAILABLE | error status=1, message='Error in command: oscihr.trigrearm: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Now.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `PICtrl.CtrlChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchget: Error trying to access the Generic PI Controller' |
| `PICtrl.CtrlChPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchpropsget: Error trying to access the Generic PI Controller' |
| `PICtrl.InputChGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.inputchget: Error trying to access the Generic PI Controller' |
| `PICtrl.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.onoffget: Error trying to access the Generic PI Controller' |
| `PICtrl.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.propsget: Error trying to access the Generic PI Controller' |
| `PICtrl.CtrlChPropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchpropsset: Error trying to access the Generic PI Controller' |
| `PICtrl.CtrlChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.ctrlchset: Error trying to access the Generic PI Controller' |
| `PICtrl.InputChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.inputchset: Error trying to access the Generic PI Controller' |
| `PICtrl.OnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.onoffset: Error trying to access the Generic PI Controller' |
| `PICtrl.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pictrl.propsset: Error trying to access the Generic PI Controller' |
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
| `PLL.AddOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.addonoffset: Module not available' |
| `PLL.AmpCtrlBandwidthSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlbandwidthset: Module not available' |
| `PLL.AmpCtrlGainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlgainset: Module not available' |
| `PLL.AmpCtrlOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlonoffset: Module not available' |
| `PLL.AmpCtrlSetpntSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlsetpntset: Module not available' |
| `PLL.CenterFreqSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.centerfreqset: Module not available' |
| `PLL.ExcRangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excrangeset: Module not available' |
| `PLL.ExcitationSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excitationset: Module not available' |
| `PLL.FreqExcOverwriteSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqexcoverwriteset: Feature not available' |
| `PLL.FreqRangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqrangeset: Module not available' |
| `PLL.FreqShiftSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftset: Module not available' |
| `PLL.InpCalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inpcalibrset: Module not available' |
| `PLL.InpPropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inppropsset: Module not available' |
| `PLL.InpRangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inprangeset: Module not available' |
| `PLL.OutOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.outonoffset: Module not available' |
| `PLL.PhasCtrlBandwidthSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlbandwidthset: Module not available' |
| `PLL.PhasCtrlGainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlgainset: Module not available' |
| `PLL.PhasCtrlOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlonoffset: Module not available' |
| `PLL.FreqShiftAutoCenter` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftautocenter: Module not available' |
| `PLL.PerfectPLLApply` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.perfectpllapply: Module not available' |
| `PLL.PerfectPLLUpdtZTC` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.perfectpllupdtztc: Module not available' |
| `PLLFreqSwp.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.open: NeedModule_viaHandler.vi:6620037<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620037\r\n     ProgrInterf FrqSweep Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `PLLFreqSwp.ParamsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.paramsget: Sweep Module not available' |
| `PLLFreqSwp.ParamsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.paramsset: Sweep Module not available' |
| `PLLFreqSwp.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.stop: Sweep Module not available' |
| `PLLPhasSwp.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllphasswp.stop: Sweep Module not available' |
| `Pattern.PropsSet` | NANONIS_ERROR | error status=1, message='Error in command: pattern.propsset: The selected experiment is not valid' |
| `Script.Open` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.open: NeedModule_viaHandler.vi:6620022<ERR>\nModule Scripting Tool not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620022\r\n     ProgrInterf Script Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `Script.ChsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.chsget: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.DataGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.dataget: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.ChsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.chsset: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.stop: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.Autosave` | NANONIS_ERROR | error status=1, message='Error in command: script.autosave: Error trying to read the Message from the Client.' |
| `Script.Deploy` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.deploy: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.LUTDeploy` | NANONIS_ERROR | error status=1, message='Error in command: script.lutdeploy: Enqueue Element in ProgrInterf Script LUT Deploy.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `Script.LUTLoad` | NANONIS_ERROR | error status=1, message='Error in command: script.lutload: Not a valid path' |
| `Script.LUTOpen` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.lutopen: NeedModule_viaHandler.vi:6620023<ERR>\nModule Script-LUT.vi not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620023\r\n     ProgrInterf Script LUT Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `Script.LUTSave` | NANONIS_ERROR | error status=1, message='Error in command: script.lutsave: Not a valid path' |
| `Script.Load` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.load: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.Run` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.run: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.Save` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.save: Cannot access the script module. \nPlease make sure it is running.' |
| `Script.Undeploy` | MODULE_UNAVAILABLE | error status=1, message='Error in command: script.undeploy: Cannot access the script module. \nPlease make sure it is running.' |
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
| `SpectrumAnlzr.ACCouplingSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.accouplingset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.AveragSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.averagset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.ChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.chset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.CursorPosSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.cursorposset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FFTWindowSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.fftwindowset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FreqRangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.freqrangeset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.FreqResSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.freqresset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.' |
| `SpectrumAnlzr.Run` | MODULE_UNAVAILABLE | error status=1, message='Error in command: spectrumanlzr.run: NeedModule_viaHandler.vi:6620035<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620035\r\n     ProgrInterf SpectrumAnalyzer Run.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi' |
| `TCPLog.StatusGet` | MODULE_UNAVAILABLE | error status=65536, message='ror in command: tcplog.statusget: Generate User Event in ProgInterf TCPLogger_Status.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TCPLog.ChsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tcplog.chsset: Generate User Event in ProgInterf TCPLogger_Set Selection.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TCPLog.OversamplSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tcplog.oversamplset: Generate User Event in ProgInterf TCPLogger_Set Oversampling.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TCPLog.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tcplog.stop: Generate User Event in ProgInterf TCPLogger_Stop.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TipRec.BufferSizeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tiprec.buffersizeget: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.' |
| `TipRec.DataGet` | EMPTY_RESPONSE | controller returned a successful empty trailer but omitted all declared response fields |
| `TipRec.BufferSizeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tiprec.buffersizeset: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.' |
| `TipRec.BufferClear` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tiprec.bufferclear: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.' |
| `TipRec.DataSave` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tiprec.datasave: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.' |
| `TipShaper.PropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.propsget: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |
| `TipShaper.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.propsset: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |
| `UserIn.CalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userin.calibrset: Cannot access the input channel 0. \nPlease make sure this input is not reserved by the Nanonis software (like Current...). To access the reserved channels, use the corresponding VI function.' |
| `UserOut.LimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.limitsget: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `UserOut.CalcSignalConfigSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.calcsignalconfigset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `UserOut.CalcSignalNameSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.calcsignalnameset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `UserOut.CalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.calibrset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `UserOut.LimitsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.limitsset: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `UserOut.ModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.modeset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `UserOut.MonitorChSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.monitorchset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `UserOut.ValSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: userout.valset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).' |
| `Util.SessionPathSet` | NANONIS_ERROR | error status=1, message='Error in command: util.sessionpathset: Session Path not valid.' |
| `Util.LayoutLoad` | NANONIS_ERROR | error status=1, message='Error in command: util.layoutload: The specified layout file does not exist' |
| `Util.LayoutSave` | NANONIS_ERROR | error status=1, message='Error in command: util.layoutsave: The specified layout file does not exist' |
| `Util.SettingsLoad` | NANONIS_ERROR | error status=1, message='Error in command: util.settingsload: The specified settings file does not exist' |
| `Util.SettingsSave` | NANONIS_ERROR | error status=1, message='Error in command: util.settingssave: The specified settings file does not exist' |
| `ZCtrl.LimitsSet` | NANONIS_ERROR | error status=1, message='Error in command: zctrl.limitsset: The limits cannot be applied because the limitation of the Z position is not enabled yet' |
| `BiasSwp.Start` | NANONIS_ERROR | error status=1, message="Error in command: biasswp.start: Bias Sweep can't be started because some\nsettings are bad.\n\nPlease check that:\n- at least one channel to record is selected.\n- upper limit > lower limit." |
| `DataLog.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: datalog.start: Cannot access the Data Logger module. \nPlease make sure it is running.' |
| `FunGen1Ch.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen1ch.start: Could not access controls. Check if the Function Generator is running.' |
| `FunGen2Ch.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: fungen2ch.start: Could not access controls. Check if the Function Generator is running.' |
| `GenSwp.Start` | NANONIS_ERROR | error status=1, message='Error in command: genswp.start: Generic Sweep can\'t be started because some\nsettings are bad.\n\nPlease check that:\n- the "signal to sweep" is selected.\n- at least one channel to record is selected.\n- upper limit > lower limit.' |
| `HSSwp.Start` | CONNECTION_ERROR | NanonisTimeoutError: Response timed out |
| `PLLFreqSwp.Start` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host |
| `PLLPhasSwp.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllphasswp.start: Sweep Module not available' |
| `TCPLog.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tcplog.start: Generate User Event in ProgInterf TCPLogger_Start.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi' |
| `TipShaper.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.start: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |

## Per-failure analysis

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

### `BeamDefl.HorConfigSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `('', '', 0.0, 0.0)`
- detail: error status=1, message='Error in command: beamdefl.horconfigset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.IntConfigSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `('', '', 0.0, 0.0)`
- detail: error status=1, message='Error in command: beamdefl.intconfigset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.VerConfigSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `('', '', 0.0, 0.0)`
- detail: error status=1, message='Error in command: beamdefl.verconfigset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BeamDefl.AutoOffset`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: beamdefl.autooffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BiasSpectr.MLSLockinPerSegGet`  (NANONIS_ERROR)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: biasspectr.mlslockinpersegget: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `BiasSpectr.MLSLockinPerSegSet`  (NANONIS_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: biasspectr.mlslockinpersegset: Bias spectroscopy module is not in multi segment mode.  It must be explicitly set before calling this command'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `BiasSpectr.MLSValsSet`  (NANONIS_ERROR)
- send args: 8, recv args: 0
- sent values: `(1, array([-1.], dtype='>f4'), array([1.], dtype='>f4'), array([0.], dtype='>f4'), array([5.e-05], dtype='>f4'), array([5.e-05], dtype='>f4'), array([64], dtype='>i4'), array([0], dtype='>u4'))`
- detail: error status=1, message='Error in command: biasspectr.mlsvalsset: Bias spectroscopy module is not in multi segment mode.  This must be explicitly set before calling this command'
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

### `DataLog.Open`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.open: NeedModule_viaHandler.vi:6620030<ERR>\nModule Data Logger not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620030\r\n     ProgrInterf DataLogger Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
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

### `DataLog.ChsSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, [])`
- detail: error status=1, message='Error in command: datalog.chsset: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `DataLog.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 10, recv args: 0
- sent values: `(0, 0, 0, 0.0, 0, '', '', 0, 0, [])`
- detail: error status=1, message='Error in command: datalog.propsset: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `DataLog.Stop`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.stop: Cannot access the Data Logger module. \nPlease make sure it is running.'
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

### `FunGen1Ch.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0.0, 0.0, 0, 0)`
- detail: error status=1, message='Error in command: fungen1ch.propsset: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen1Ch.Stop`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: fungen1ch.stop: Could not access controls. Check if the Function Generator is running.'
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

### `FunGen2Ch.OnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: fungen2ch.onoffset: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 6, recv args: 0
- sent values: `(0, 0.0, 0.0, 0, 0, 0)`
- detail: error status=1, message='Error in command: fungen2ch.propsset: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.SignalSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: fungen2ch.signalset: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.WaveformSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: fungen2ch.waveformset: Could not access the selected channel. Check if the index is valid.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.Stop`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: fungen2ch.stop: Could not access controls. Check if the Function Generator is running.'
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

### `GenPICtrl.AOPropsSet`  (MODULE_UNAVAILABLE)
- send args: 6, recv args: 0
- sent values: `('', '', 0.0, 0.0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: genpictrl.aopropsset: Property Node in ProgrInterf GenericPICtrl AOChProperties Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenPICtrl.DemodChSet`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: genpictrl.demodchset: Enqueue Element in ProgrInterf GenericPICtrl DemodSignal Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `GenPICtrl.ModChSet`  (NANONIS_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: genpictrl.modchset: Enqueue Element in ProgrInterf GenericPICtrl ModSignal Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `GenPICtrl.OnOffSet`  (NANONIS_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: genpictrl.onoffset: Enqueue Element in ProgrInterf GenericPICtrl Status Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `GenPICtrl.PropsSet`  (NANONIS_ERROR)
- send args: 4, recv args: 0
- sent values: `(0.0, 0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: genpictrl.propsset: Enqueue Element in ProgrInterf GenericPICtrl Properties Set.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

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

### `HSSwp.AcqChsSet`  (CONNECTION_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, [])`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.AutoReverseSet`  (CONNECTION_ERROR)
- send args: 8, recv args: 0
- sent values: `(0, 0, 0, 0.0, 0, 0, 0, 0.0)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.EndSettlSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.NumSweepsSet`  (CONNECTION_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.ResetSignalsSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SaveBasenameSet`  (CONNECTION_ERROR)
- send args: 2, recv args: 0
- sent values: `('', '')`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SaveDataSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SaveOptionsSet`  (CONNECTION_ERROR)
- send args: 4, recv args: 0
- sent values: `('', 0, 0, [])`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChBwdDelaySet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChBwdSwSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChLimitsSet`  (CONNECTION_ERROR)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChNumPtsSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChSignalSet`  (CONNECTION_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.SwpChTimingSet`  (CONNECTION_ERROR)
- send args: 4, recv args: 0
- sent values: `(0.0, 0.0, 0.0, 0.0)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.ZCtrlOffSet`  (CONNECTION_ERROR)
- send args: 5, recv args: 0
- sent values: `(0, 0, 0.0, 0.0, 0.0)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `HSSwp.Stop`  (CONNECTION_ERROR)
- send args: 0, recv args: 0
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlOnOffGet`  (CONNECTION_ERROR)
- send args: 0, recv args: 1
- sent values: `()`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlPropsGet`  (CONNECTION_ERROR)
- send args: 0, recv args: 3
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.ValGet`  (CONNECTION_ERROR)
- send args: 0, recv args: 1
- sent values: `()`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.WPiezoGet`  (CONNECTION_ERROR)
- send args: 0, recv args: 1
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlOnOffSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlPropsSet`  (CONNECTION_ERROR)
- send args: 3, recv args: 0
- sent values: `(0.0, 0.0, 0)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.WPiezoSet`  (CONNECTION_ERROR)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlCalibrOpen`  (CONNECTION_ERROR)
- send args: 0, recv args: 0
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `Interf.CtrlNullDefl`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: interf.ctrlnulldefl: Cannot access the Interferometer module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Interf.CtrlReset`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: interf.ctrlreset: Cannot access the Interferometer module. \nPlease make sure it is running.'
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

### `KelvinCtrl.BiasLimitsSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0.0, 0.0)`
- detail: error status=1, message='Error in command: kelvinctrl.biaslimitsset: Could not access controls. Check if the module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.CtrlOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: kelvinctrl.ctrlonoffset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.CtrlSignalSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: kelvinctrl.ctrlsignalset: Could not access controls. Check if the module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.GainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: kelvinctrl.gainset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.ModOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: kelvinctrl.modonoffset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.ModParamsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0.0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: kelvinctrl.modparamsset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `KelvinCtrl.SetpntSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: error status=1, message='Error in command: kelvinctrl.setpntset: Cannot access the Kelvin Controller module. \nPlease make sure it is running.'
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

### `Laser.OnOffSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: laser.onoffset: Cannot access the Laser Control module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Laser.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: error status=1, message='Error in command: laser.propsset: Cannot access the Laser Control module. \nPlease make sure it is running.'
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

### `MCVA5.ContStateUpdateSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.contstateupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContTempUpdateSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.conttempupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.CouplingSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.couplingset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.GainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.gainset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.InputModeSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.inputmodeset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.UserInSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.userinset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.SingleStateUpdate`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 8
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.singlestateupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.SingleTempUpdate`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 4
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.singletempupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.'
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

### `MProbeBias.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobebias.calibrset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.RangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mprobebias.rangeset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.Set`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: mprobebias.set: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.Pulse`  (MODULE_UNAVAILABLE)
- send args: 6, recv args: 0
- sent values: `(0, 0, 0.0, 0.0, 0, 0)`
- detail: error status=1, message='Error in command: mprobebias.pulse: Incorrect Scanner Index'
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

### `MProbeCurrent.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0.0, 0.0)`
- detail: error status=0, message='Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeCurrent.GainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
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

### `MProbeScanner.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0.0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobescanner.calibrset: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.SpeedSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: mprobescanner.speedset: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.XYPosSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobescanner.xyposset: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.Stop`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobescanner.stop: Invalid scanner number'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeScanner.ScannerSwitch`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobescanner.scannerswitch: Invalid scanner number'
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

### `MProbeZCtrl.GainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobezctrl.gainset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.HomePropsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0.0)`
- detail: error status=1, message='Error in command: mprobezctrl.homepropsset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.LimitsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobezctrl.limitsset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.OnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mprobezctrl.onoffset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.SetpntSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: mprobezctrl.setpntset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.ZPosSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: mprobezctrl.zposset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.Home`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.home: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeZCtrl.Withdraw`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobezctrl.withdraw: Incorrect Scanner Index'
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

### `Osci1T.ChSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci1t.chset: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.TimebaseSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci1t.timebaseset: Cannot access the Oscilloscope. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci1T.TrigSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: osci1t.trigset: Cannot access the Oscilloscope. \nPlease make sure it is running.'
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

### `Osci2T.ChsSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: osci2t.chsset: Cannot access the Oscilloscope 2T . \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.OversamplSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci2t.oversamplset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.TimebaseSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: osci2t.timebaseset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Osci2T.TrigSet`  (MODULE_UNAVAILABLE)
- send args: 6, recv args: 0
- sent values: `(0, 0, 0, 0.0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: osci2t.trigset: Cannot access the Oscilloscope 2T. \nPlease make sure it is running.'
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

### `OsciHR.CalibrModeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: oscihr.calibrmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Calibration mode.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.ChSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: oscihr.chset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Channel v3.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.OversamplSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.oversamplset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Oversampling.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDAvrgCountSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.psdavrgcountset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Count.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDAvrgTypeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.psdavrgtypeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Averaging.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDWeightSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.psdweightset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Weighting.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDWindowSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.psdwindowset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Window.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PreTrigSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: oscihr.pretrigset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Pretrigger.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.SamplesSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.samplesset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Samples.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigArmModeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.trigarmmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Mode.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigDigChSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.trigdigchset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Digital Trigger Channel.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigDigSlopeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.trigdigslopeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Digital Trigger Polarity.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevChSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.triglevchset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set LEvel Trigger Channel v3.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevHystSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: error status=1, message='Error in command: oscihr.triglevhystset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Hysteresis.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevSlopeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.triglevslopeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Polarity.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigLevValSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0.0,)`
- detail: error status=1, message='Error in command: oscihr.triglevvalset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Level Trigger Level.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigModeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.trigmodeset: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Type.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDAvrgRestart`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.psdavrgrestart: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set PSD Restart.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.PSDShow`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: oscihr.psdshow: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Show PSD.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.Run`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.run: NeedModule_viaHandler.vi:6620033<ERR>\nModule Oscilloscope - High-Resolution not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620033\r\n     ProgrInterf Osci FPGA Run.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `OsciHR.TrigRearm`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: oscihr.trigrearm: Generate User Event in OSCI-HR-Get API (no Ref Validity check).vi->ProgrInterf Osci FPGA Set Trigger Now.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
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

### `PICtrl.CtrlChPropsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pictrl.ctrlchpropsset: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.CtrlChSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pictrl.ctrlchset: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.InputChSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pictrl.inputchset: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.OnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pictrl.onoffset: Error trying to access the Generic PI Controller'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PICtrl.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 5, recv args: 0
- sent values: `(0, 0.0, 0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: pictrl.propsset: Error trying to access the Generic PI Controller'
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

### `PLL.AddOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.addonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlBandwidthSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.ampctrlbandwidthset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlGainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pll.ampctrlgainset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.ampctrlonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlSetpntSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.ampctrlsetpntset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.CenterFreqSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.centerfreqset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcRangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.excrangeset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcitationSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.excitationset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqExcOverwriteSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: pll.freqexcoverwriteset: Feature not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqRangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.freqrangeset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.freqshiftset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpCalibrSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.inpcalibrset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpPropsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: pll.inppropsset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpRangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.inprangeset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.OutOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.outonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlBandwidthSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.phasctrlbandwidthset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlGainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pll.phasctrlgainset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.phasctrlonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftAutoCenter`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqshiftautocenter: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PerfectPLLApply`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.perfectpllapply: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PerfectPLLUpdtZTC`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.perfectpllupdtztc: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.Open`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.open: NeedModule_viaHandler.vi:6620037<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620037\r\n     ProgrInterf FrqSweep Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.ParamsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.paramsget: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.ParamsSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pllfreqswp.paramsset: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.Stop`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.stop: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLPhasSwp.Stop`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllphasswp.stop: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Pattern.PropsSet`  (NANONIS_ERROR)
- send args: 5, recv args: 0
- sent values: `('', '', '', 0.0, 0)`
- detail: error status=1, message='Error in command: pattern.propsset: The selected experiment is not valid'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.Open`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: script.open: NeedModule_viaHandler.vi:6620022<ERR>\nModule Scripting Tool not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620022\r\n     ProgrInterf Script Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
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

### `Script.ChsSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, [])`
- detail: error status=1, message='Error in command: script.chsset: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Stop`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: script.stop: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Autosave`  (NANONIS_ERROR)
- send args: 5, recv args: 0
- sent values: `(0, 0, 0, '', '')`
- detail: error status=1, message='Error in command: script.autosave: Error trying to read the Message from the Client.'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.Deploy`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: script.deploy: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.LUTDeploy`  (NANONIS_ERROR)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: script.lutdeploy: Enqueue Element in ProgrInterf Script LUT Deploy.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.LUTLoad`  (NANONIS_ERROR)
- send args: 4, recv args: 0
- sent values: `(0, '', 0, [])`
- detail: error status=1, message='Error in command: script.lutload: Not a valid path'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.LUTOpen`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: script.lutopen: NeedModule_viaHandler.vi:6620023<ERR>\nModule Script-LUT.vi not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620023\r\n     ProgrInterf Script LUT Open.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.LUTSave`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, '')`
- detail: error status=1, message='Error in command: script.lutsave: Not a valid path'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.Load`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, '', 0)`
- detail: error status=1, message='Error in command: script.load: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Run`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: script.run: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Save`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, '', 0)`
- detail: error status=1, message='Error in command: script.save: Cannot access the script module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Script.Undeploy`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: script.undeploy: Cannot access the script module. \nPlease make sure it is running.'
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

### `SpectrumAnlzr.ACCouplingSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.accouplingset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.AveragSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.averagset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.ChSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.chset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.CursorPosSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: spectrumanlzr.cursorposset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FFTWindowSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.fftwindowset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FreqRangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.freqrangeset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.FreqResSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: spectrumanlzr.freqresset: Cannot access the Spectrum Analyzer. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `SpectrumAnlzr.Run`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: spectrumanlzr.run: NeedModule_viaHandler.vi:6620035<ERR>\nModule  not found.\n\n\n<b>Complete call chain:</b>\r\n     NeedModule_viaHandler.vi:6620035\r\n     ProgrInterf SpectrumAnalyzer Run.vi\r\n     ExecuteFunction.vi:3140003\r\n     TCP Server-ProcessCmd.vi:4960002\r\n     TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.StatusGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=65536, message='ror in command: tcplog.statusget: Generate User Event in ProgInterf TCPLogger_Status.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.ChsSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, [])`
- detail: error status=1, message='Error in command: tcplog.chsset: Generate User Event in ProgInterf TCPLogger_Set Selection.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.OversamplSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: tcplog.oversamplset: Generate User Event in ProgInterf TCPLogger_Set Oversampling.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.Stop`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: tcplog.stop: Generate User Event in ProgInterf TCPLogger_Stop.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
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

### `TipRec.BufferSizeSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: tiprec.buffersizeset: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipRec.BufferClear`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: tiprec.bufferclear: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipRec.DataSave`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, '')`
- detail: error status=1, message='Error in command: tiprec.datasave: Cannot access the Tip Move Recorder module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipShaper.PropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 11
- sent values: `()`
- detail: error status=1, message='Error in command: tipshaper.propsget: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipShaper.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 11, recv args: 0
- sent values: `(0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: tipshaper.propsset: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserIn.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: userin.calibrset: Cannot access the input channel 0. \nPlease make sure this input is not reserved by the Nanonis software (like Current...). To access the reserved channels, use the corresponding VI function.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.LimitsGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 2
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: userout.limitsget: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.CalcSignalConfigSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0, 0, 0)`
- detail: error status=1, message='Error in command: userout.calcsignalconfigset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.CalcSignalNameSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, '')`
- detail: error status=1, message='Error in command: userout.calcsignalnameset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: userout.calibrset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.LimitsSet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 0
- sent values: `(0, 0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: userout.limitsset: Generate User Event in ProgrInterf UserOutput Limits GetSet.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.ModeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: userout.modeset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.MonitorChSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: userout.monitorchset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `UserOut.ValSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: userout.valset: Cannot access the output channel 0. \nPlease make sure this output is not reserved by the Nanonis software (like Bias, X, Y, Z...). To access the reserved channels, use the corresponding VI function (e.g. Set Bias).'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Util.SessionPathSet`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `('', 0)`
- detail: error status=1, message='Error in command: util.sessionpathset: Session Path not valid.'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.LayoutLoad`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `('', 0)`
- detail: error status=1, message='Error in command: util.layoutload: The specified layout file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.LayoutSave`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `('', 0)`
- detail: error status=1, message='Error in command: util.layoutsave: The specified layout file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.SettingsLoad`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `('', 0)`
- detail: error status=1, message='Error in command: util.settingsload: The specified settings file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.SettingsSave`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `('', 0)`
- detail: error status=1, message='Error in command: util.settingssave: The specified settings file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `ZCtrl.LimitsSet`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `(7.500000265281415e-07, -7.500000265281415e-07)`
- detail: error status=1, message='Error in command: zctrl.limitsset: The limits cannot be applied because the limitation of the Z position is not enabled yet'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `BiasSwp.Start`  (NANONIS_ERROR)
- send args: 5, recv args: 6
- sent values: `(0, 0, 0, '', 0)`
- detail: error status=1, message="Error in command: biasswp.start: Bias Sweep can't be started because some\nsettings are bad.\n\nPlease check that:\n- at least one channel to record is selected.\n- upper limit > lower limit."
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `DataLog.Start`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: datalog.start: Cannot access the Data Logger module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen1Ch.Start`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: fungen1ch.start: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `FunGen2Ch.Start`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: fungen2ch.start: Could not access controls. Check if the Function Generator is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `GenSwp.Start`  (NANONIS_ERROR)
- send args: 5, recv args: 6
- sent values: `(0, 0, '', 0, 0)`
- detail: error status=1, message='Error in command: genswp.start: Generic Sweep can\'t be started because some\nsettings are bad.\n\nPlease check that:\n- the "signal to sweep" is selected.\n- at least one channel to record is selected.\n- upper limit > lower limit.'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `HSSwp.Start`  (CONNECTION_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: NanonisTimeoutError: Response timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `PLLFreqSwp.Start`  (CONNECTION_ERROR)
- send args: 3, recv args: 12
- sent values: `(0, 0, 0)`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] An existing connection was forcibly closed by the remote host
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `PLLPhasSwp.Start`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 6
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pllphasswp.start: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TCPLog.Start`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 0
- sent values: `()`
- detail: error status=1, message='Error in command: tcplog.start: Generate User Event in ProgInterf TCPLogger_Start.vi->ExecuteFunction.vi:3140003->TCP Server-ProcessCmd.vi:4960002->TCP Server.vi'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipShaper.Start`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: tipshaper.start: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.
