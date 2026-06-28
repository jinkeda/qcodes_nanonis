# Nanonis Live Command Test Report

- Target: `127.0.0.1:6501`
- Config: `C:\Users\JinKeda\OneDrive\Desktop\Nanonis_STM\qcodes_nanonis-refactor-layered-architecture\configs\nanonis_tcp.yaml`
- Total commands in config: **148**
- Skipped (destructive): **1**
- Tested: **147**
- Successful: **58**
- Failed: **89**

## Breakdown by category

| Category | Count |
|----------|-------|
| PASS | 58 |
| MODULE_UNAVAILABLE | 59 |
| PROTOCOL_MISMATCH | 4 |
| NANONIS_ERROR | 8 |
| STRUCTURE_MISMATCH | 1 |
| DECODE_ERROR | 15 |
| ENCODE_ERROR | 0 |
| CONNECTION_ERROR | 2 |
| SKIPPED | 1 |

**Likely command-definition bugs (actionable): 20** — `Bias.Pulse`, `BiasSpectr.ChsGet`, `BiasSpectr.SafeCond2Get`, `Current.GainSet`, `File.datLoad`, `MProbeCurrent.Get`, `Motor.FreqAmpGet`, `Motor.PosGet`, `PLLPhasSwp.Start`, `PLLPhasSwp.Stop`, `PLLQCtrl.PhaseGet`, `Scan.FrameDataGrab`, `Scan.PropsGet`, `Scan.PropsSet`, `Script.ChsGet`, `Script.LUTDeploy`, `TCPLog.StatusGet`, `TipShaper.PropsGet`, `Util.UnLock`, `Util.VersionGet`

## Failed commands

| Command | Category | Detail |
|---------|----------|--------|
| `AutoApproach.OnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: autoapproach.onoffget: Could not access the "Auto Approach" module. Please make sure this module is running.' |
| `AutoApproach.OnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: autoapproach.onoffset: Could not access the "Auto Approach" module. Please make sure this module is running.' |
| `Bias.Pulse` | DECODE_ERROR | ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response |
| `BiasSpectr.AdvPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: biasspectr.advpropsget: Cannot access the bias spectroscopy module. \nPlease make sure it is running.' |
| `BiasSpectr.ChsGet` | STRUCTURE_MISMATCH | decoded 4 body byte(s) + 8 trailer byte(s), but response is 133 byte(s) (+121 unaccounted) |
| `BiasSpectr.ChsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: biasspectr.chsset: Cannot access the Bias Spectroscopy module. \nPlease make sure it is running.' |
| `BiasSpectr.LimitsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: biasspectr.limitsget: Cannot access the bias spectroscopy module. \nPlease make sure it is running.' |
| `BiasSpectr.PropsGet` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: timed out |
| `BiasSpectr.SafeCond1Get` | CONNECTION_ERROR | NanonisConnectionError: Receive failed: [WinError 10054] 远程主机强迫关闭了一个现有的连接。 |
| `BiasSpectr.SafeCond2Get` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Current.GainSet` | PROTOCOL_MISMATCH | error status=1, message='Error in command: current.gainset: Unflatten From String in UnflattenToInt32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `File.datLoad` | DECODE_ERROR | ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response |
| `MCVA5.ContStateUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContStateUpdateSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.contstateupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContTempUpdateGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.ContTempUpdateSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.conttempupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.CouplingGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.CouplingSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.couplingset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.GainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.GainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.gainset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.InputModeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.InputModeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.inputmodeset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.SingleStateUpdate` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.singlestateupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.SingleTempUpdate` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.singletempupdate: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.UserInGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MCVA5.UserInSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mcva5.userinset: Cannot access the Preamplifier module. \nPlease make sure it is running.' |
| `MProbeBias.CalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index' |
| `MProbeBias.CalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.calibrset: Incorrect Scanner Index' |
| `MProbeBias.Get` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index' |
| `MProbeBias.Pulse` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.pulse: Incorrect Scanner Index' |
| `MProbeBias.RangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index' |
| `MProbeBias.RangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.rangeset: Incorrect Scanner Index' |
| `MProbeBias.Set` | MODULE_UNAVAILABLE | error status=1, message='Error in command: mprobebias.set: Incorrect Scanner Index' |
| `MProbeCurrent.Get` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Motor.FreqAmpGet` | PROTOCOL_MISMATCH | error status=1165128303, message=' command: motor.freqampget: Unflatten From String in UnflattenToU16.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `Motor.PosGet` | PROTOCOL_MISMATCH | error status=1914726766, message='mand: motor.posget: Unflatten From String in UnflattenToU32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `PLL.AddOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.addonoffget: Module not available' |
| `PLL.AddOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.addonoffset: Module not available' |
| `PLL.AmpCtrlBandwidthGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlbandwidthget: Module not available' |
| `PLL.AmpCtrlGainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlgainget: Module not available' |
| `PLL.AmpCtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlonoffget: Module not available' |
| `PLL.AmpCtrlOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlonoffset: Module not available' |
| `PLL.AmpCtrlSetpntGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.ampctrlsetpntget: Module not available' |
| `PLL.ExcRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excrangeget: Module not available' |
| `PLL.ExcitationGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.excitationget: Module not available' |
| `PLL.FreqExcOverwriteGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqexcoverwriteget: Feature not available' |
| `PLL.FreqExcOverwriteSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqexcoverwriteset: Feature not available' |
| `PLL.FreqRangeGet` | MODULE_UNAVAILABLE | error status=1165128303, message=' command: pll.freqrangeget: Module not available' |
| `PLL.FreqShiftAutoCenter` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftautocenter: Module not available' |
| `PLL.FreqShiftGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftget: Module not available' |
| `PLL.FreqShiftSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.freqshiftset: Module not available' |
| `PLL.InpCalibrGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inpcalibrget: Module not available' |
| `PLL.InpCalibrSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inpcalibrset: Module not available' |
| `PLL.InpPropsGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inppropsget: Module not available' |
| `PLL.InpRangeGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inprangeget: Module not available' |
| `PLL.InpRangeSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.inprangeset: Module not available' |
| `PLL.OutOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.outonoffget: Module not available' |
| `PLL.OutOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.outonoffset: Module not available' |
| `PLL.PerfectPLLApply` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.perfectpllapply: Module not available' |
| `PLL.PerfectPLLUpdtZTC` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.perfectpllupdtztc: Module not available' |
| `PLL.PhasCtrlBandwidthGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlbandwidthget: Module not available' |
| `PLL.PhasCtrlBandwidthSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlbandwidthset: Module not available' |
| `PLL.PhasCtrlGainGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlgainget: Module not available' |
| `PLL.PhasCtrlGainSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlgainset: Module not available' |
| `PLL.PhasCtrlOnOffGet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlonoffget: Module not available' |
| `PLL.PhasCtrlOnOffSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pll.phasctrlonoffset: Module not available' |
| `PLLFreqSwp.Stop` | MODULE_UNAVAILABLE | error status=1, message='Error in command: pllfreqswp.stop: Sweep Module not available' |
| `PLLPhasSwp.Start` | DECODE_ERROR | ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response |
| `PLLPhasSwp.Stop` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `PLLQCtrl.PhaseGet` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Scan.FrameDataGrab` | DECODE_ERROR | UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb8 in position 15: invalid start byte |
| `Scan.PropsGet` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Scan.PropsSet` | PROTOCOL_MISMATCH | error status=1, message='Error in command: scan.propsset: Unflatten From String in UnflattenToU32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `Script.Autosave` | NANONIS_ERROR | error status=1, message='Error in command: script.autosave: Error trying to read the Message from the Client.' |
| `Script.ChsGet` | DECODE_ERROR | ValueError: buffer size must be a multiple of element size |
| `Script.LUTDeploy` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Script.LUTLoad` | NANONIS_ERROR | error status=1, message='Error in command: script.lutload: Not a valid path' |
| `Script.LUTSave` | NANONIS_ERROR | error status=1, message='Error in command: script.lutsave: Not a valid path' |
| `TCPLog.OversamplSet` | NANONIS_ERROR | error status=1, message='Error in command: tcplog.oversamplset: Generate User Event in ProgInterf TCPLogger_Set Oversampling.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `TCPLog.StatusGet` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `TCPLog.Stop` | NANONIS_ERROR | error status=1, message='Error in command: tcplog.stop: Generate User Event in ProgInterf TCPLogger_Stop.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi' |
| `TipShaper.PropsGet` | DECODE_ERROR | ValueError: buffer size must be a multiple of element size |
| `TipShaper.PropsSet` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.propsset: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |
| `TipShaper.Start` | MODULE_UNAVAILABLE | error status=1, message='Error in command: tipshaper.start: Cannot access the Tip Shaper module. \nPlease make sure it is running.' |
| `Util.SessionPathSet` | NANONIS_ERROR | error status=1, message='Error in command: util.sessionpathset: Session Path not valid.' |
| `Util.SettingsLoad` | NANONIS_ERROR | error status=1, message='Error in command: util.settingsload: The specified settings file does not exist' |
| `Util.SettingsSave` | NANONIS_ERROR | error status=1, message='Error in command: util.settingssave: The specified settings file does not exist' |
| `Util.UnLock` | DECODE_ERROR | error: unpack requires a buffer of 4 bytes |
| `Util.VersionGet` | DECODE_ERROR | UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc1 in position 3: invalid start byte |

## Per-failure analysis

### `AutoApproach.OnOffGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 1
- sent values: `()`
- detail: error status=1, message='Error in command: autoapproach.onoffget: Could not access the "Auto Approach" module. Please make sure this module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `AutoApproach.OnOffSet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: autoapproach.onoffset: Could not access the "Auto Approach" module. Please make sure this module is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Bias.Pulse`  (DECODE_ERROR)
- send args: 55, recv args: 59
- sent values: `(0, 0.0, 0.0, 0, 0, 0, 0, 0, '', 0, 0, 0, 0, 0, 0.0, 0.0, 0, [], 0, 0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0, '', '', 0, [], [], [], 0)`
- detail: ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `BiasSpectr.AdvPropsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 4
- sent values: `()`
- detail: error status=1, message='Error in command: biasspectr.advpropsget: Cannot access the bias spectroscopy module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BiasSpectr.ChsGet`  (STRUCTURE_MISMATCH)
- send args: 0, recv args: 2
- sent values: `()`
- detail: decoded 4 body byte(s) + 8 trailer byte(s), but response is 133 byte(s) (+121 unaccounted)
- likely reason: Response decoded but byte count differs from the definition - the recv definition has too many/few fields or a wrong type.

### `BiasSpectr.ChsSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, [])`
- detail: error status=1, message='Error in command: biasspectr.chsset: Cannot access the Bias Spectroscopy module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BiasSpectr.LimitsGet`  (MODULE_UNAVAILABLE)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1, message='Error in command: biasspectr.limitsget: Cannot access the bias spectroscopy module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `BiasSpectr.PropsGet`  (CONNECTION_ERROR)
- send args: 0, recv args: 13
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: timed out
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `BiasSpectr.SafeCond1Get`  (CONNECTION_ERROR)
- send args: 0, recv args: 4
- sent values: `()`
- detail: NanonisConnectionError: Receive failed: [WinError 10054] 远程主机强迫关闭了一个现有的连接。
- likely reason: No/short response - command may block (wait-until-done), be unsupported, or have crashed the connection.

### `BiasSpectr.SafeCond2Get`  (DECODE_ERROR)
- send args: 181, recv args: 233
- sent values: `(0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0, 0, 0, 0.0, 0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0, '', 0, [], 0, 0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, [], [], 0, [], [], '', '', 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, '', '', '', '', 0, 0, [], 0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0.0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, [], [], '', '', 0, 0.0, 0.0, 0, '', 0, '', 0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Current.GainSet`  (PROTOCOL_MISMATCH)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: current.gainset: Unflatten From String in UnflattenToInt32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis could not unflatten the request body -> the command's SEND argument types/order/count in the YAML do not match the real protocol. Fix the send definition.

### `File.datLoad`  (DECODE_ERROR)
- send args: 3, recv args: 9
- sent values: `('', '', 0)`
- detail: ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `MCVA5.ContStateUpdateGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.contstateupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContStateUpdateSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.contstateupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContTempUpdateGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mcva5.conttempupdateget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.ContTempUpdateSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.conttempupdateset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.CouplingGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.couplingget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.CouplingSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.couplingset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.GainGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.gainget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.GainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.gainset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.InputModeGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.inputmodeget: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.InputModeSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.inputmodeset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
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

### `MCVA5.UserInGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: mcva5.useringet: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MCVA5.UserInSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: mcva5.userinset: Cannot access the Preamplifier module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.CalibrGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.calibrget: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.CalibrSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: mprobebias.calibrset: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.Get`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.get: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.Pulse`  (MODULE_UNAVAILABLE)
- send args: 6, recv args: 0
- sent values: `(0, 0, 0.0, 0.0, 0, 0)`
- detail: error status=1, message='Error in command: mprobebias.pulse: Incorrect Scanner Index'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `MProbeBias.RangeGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: mprobebias.rangeget: Incorrect Scanner Index'
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

### `MProbeCurrent.Get`  (DECODE_ERROR)
- send args: 20, recv args: 30
- sent values: `(0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Motor.FreqAmpGet`  (PROTOCOL_MISMATCH)
- send args: 0, recv args: 2
- sent values: `()`
- detail: error status=1165128303, message=' command: motor.freqampget: Unflatten From String in UnflattenToU16.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis could not unflatten the request body -> the command's SEND argument types/order/count in the YAML do not match the real protocol. Fix the send definition.

### `Motor.PosGet`  (PROTOCOL_MISMATCH)
- send args: 0, recv args: 3
- sent values: `()`
- detail: error status=1914726766, message='mand: motor.posget: Unflatten From String in UnflattenToU32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis could not unflatten the request body -> the command's SEND argument types/order/count in the YAML do not match the real protocol. Fix the send definition.

### `PLL.AddOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.addonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AddOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.addonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlBandwidthGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlbandwidthget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlGainGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 3
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.ampctrlgainget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 1
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pll.ampctrlonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.ampctrlonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.AmpCtrlSetpntGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.ampctrlsetpntget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcRangeGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.excrangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.ExcitationGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.excitationget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqExcOverwriteGet`  (MODULE_UNAVAILABLE)
- send args: 4, recv args: 2
- sent values: `(0, 0, 0, 0)`
- detail: error status=1, message='Error in command: pll.freqexcoverwriteget: Feature not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqExcOverwriteSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: pll.freqexcoverwriteset: Feature not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqRangeGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 2
- sent values: `(0, 0.0)`
- detail: error status=1165128303, message=' command: pll.freqrangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftAutoCenter`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqshiftautocenter: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.freqshiftget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.FreqShiftSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.freqshiftset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpCalibrGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.inpcalibrget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpCalibrSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.inpcalibrset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpPropsGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 2
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.inppropsget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpRangeGet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 1
- sent values: `(0, 0, 0)`
- detail: error status=1, message='Error in command: pll.inprangeget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.InpRangeSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.inprangeset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.OutOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.outonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.OutOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.outonoffset: Module not available'
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

### `PLL.PhasCtrlBandwidthGet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 1
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.phasctrlbandwidthget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlBandwidthSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0.0)`
- detail: error status=1, message='Error in command: pll.phasctrlbandwidthset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlGainGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 3
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.phasctrlgainget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlGainSet`  (MODULE_UNAVAILABLE)
- send args: 3, recv args: 0
- sent values: `(0, 0.0, 0.0)`
- detail: error status=1, message='Error in command: pll.phasctrlgainset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlOnOffGet`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 1
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pll.phasctrlonoffget: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLL.PhasCtrlOnOffSet`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: pll.phasctrlonoffset: Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLFreqSwp.Stop`  (MODULE_UNAVAILABLE)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: pllfreqswp.stop: Sweep Module not available'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `PLLPhasSwp.Start`  (DECODE_ERROR)
- send args: 2, recv args: 6
- sent values: `(0, 0)`
- detail: ValueError: Array requires 1 preceding integer size argument(s), but only 0 were found in the response
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `PLLPhasSwp.Stop`  (DECODE_ERROR)
- send args: 26, recv args: 31
- sent values: `(0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, '', '', 0, 0, 0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `PLLQCtrl.PhaseGet`  (DECODE_ERROR)
- send args: 6, recv args: 16
- sent values: `(0, 0, 0.0, 0.0, 0, 0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Scan.FrameDataGrab`  (DECODE_ERROR)
- send args: 2, recv args: 6
- sent values: `(0, 0)`
- detail: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb8 in position 15: invalid start byte
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Scan.PropsGet`  (DECODE_ERROR)
- send args: 0, recv args: 16
- sent values: `()`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Scan.PropsSet`  (PROTOCOL_MISMATCH)
- send args: 7, recv args: 0
- sent values: `(0, 0, 0, 0, '', 0, '')`
- detail: error status=1, message='Error in command: scan.propsset: Unflatten From String in UnflattenToU32.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis could not unflatten the request body -> the command's SEND argument types/order/count in the YAML do not match the real protocol. Fix the send definition.

### `Script.Autosave`  (NANONIS_ERROR)
- send args: 7, recv args: 0
- sent values: `(0, 0, 0, '', '', '', '')`
- detail: error status=1, message='Error in command: script.autosave: Error trying to read the Message from the Client.'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.ChsGet`  (DECODE_ERROR)
- send args: 4, recv args: 5
- sent values: `(0, 0, [], 0)`
- detail: ValueError: buffer size must be a multiple of element size
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Script.LUTDeploy`  (DECODE_ERROR)
- send args: 60, recv args: 64
- sent values: `(0, 0, 0, 0, 0.0, 0.0, 0, 0.0, 0.0, '', '', '', '', 0.0, 0.0, 0, 0, 0, 0, [], 0, 0, 0, 0.0, 0.0, 0, 0, 0, 0.0, '', '', 0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0, [], 0, 0, 0, 0.0, 0, '', '', '', '', '', '', [])`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Script.LUTLoad`  (NANONIS_ERROR)
- send args: 5, recv args: 0
- sent values: `(0, '', '', 0, [])`
- detail: error status=1, message='Error in command: script.lutload: Not a valid path'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Script.LUTSave`  (NANONIS_ERROR)
- send args: 3, recv args: 0
- sent values: `(0, '', '')`
- detail: error status=1, message='Error in command: script.lutsave: Not a valid path'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `TCPLog.OversamplSet`  (NANONIS_ERROR)
- send args: 1, recv args: 0
- sent values: `(0,)`
- detail: error status=1, message='Error in command: tcplog.oversamplset: Generate User Event in ProgInterf TCPLogger_Set Oversampling.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `TCPLog.StatusGet`  (DECODE_ERROR)
- send args: 53, recv args: 67
- sent values: `(0, 0, 0, 0, 0, 0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0.0, 0, 0, 0.0, 0, 0, 0.0, 0, 0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `TCPLog.Stop`  (NANONIS_ERROR)
- send args: 2, recv args: 0
- sent values: `(0, [])`
- detail: error status=1, message='Error in command: tcplog.stop: Generate User Event in ProgInterf TCPLogger_Stop.vi->ExecuteFunction.vi:3140005->TCP Server-Receive-Execute-Send.vi:1410004->TCP Server.vi'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `TipShaper.PropsGet`  (DECODE_ERROR)
- send args: 120, recv args: 140
- sent values: `(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0.0, 0.0, 0, [], 0, 0, [], '', '', 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0, '', 0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0.0, 0, 0, 0, '', '', '', '', 0, '', '', 0, 0, [], 0, 0, 0, 0, 0.0, 0.0, 0, 0.0, 0.0, 0.0, 0, 0.0, 0, 0, 0.0, 0.0, 0.0, 0, 0.0, '', '', '', '', 0.0, 0.0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0, 0, 0.0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0.0, 0, 0, 0, 0.0, 0, 0.0, 0, 0, 0, 0.0, 0.0, 0, 0.0, 0, 0.0, 0)`
- detail: ValueError: buffer size must be a multiple of element size
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `TipShaper.PropsSet`  (MODULE_UNAVAILABLE)
- send args: 11, recv args: 0
- sent values: `(0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)`
- detail: error status=1, message='Error in command: tipshaper.propsset: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `TipShaper.Start`  (MODULE_UNAVAILABLE)
- send args: 2, recv args: 0
- sent values: `(0, 0)`
- detail: error status=1, message='Error in command: tipshaper.start: Cannot access the Tip Shaper module. \nPlease make sure it is running.'
- likely reason: The relevant module/feature/scanner is not running in this session (environment limitation). The command definition is probably fine - retest with that module enabled.

### `Util.SessionPathSet`  (NANONIS_ERROR)
- send args: 3, recv args: 0
- sent values: `('', '', 0)`
- detail: error status=1, message='Error in command: util.sessionpathset: Session Path not valid.'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.SettingsLoad`  (NANONIS_ERROR)
- send args: 3, recv args: 0
- sent values: `('', '', 0)`
- detail: error status=1, message='Error in command: util.settingsload: The specified settings file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.SettingsSave`  (NANONIS_ERROR)
- send args: 7, recv args: 0
- sent values: `('', '', 0, '', '', 0, 0)`
- detail: error status=1, message='Error in command: util.settingssave: The specified settings file does not exist'
- likely reason: Nanonis rejected the request - usually the synthesized neutral argument is out of range/invalid for this command, or the command is not available in this controller/mode.

### `Util.UnLock`  (DECODE_ERROR)
- send args: 3, recv args: 3
- sent values: `(0.0, 0.0, 0)`
- detail: error: unpack requires a buffer of 4 bytes
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).

### `Util.VersionGet`  (DECODE_ERROR)
- send args: 0, recv args: 6
- sent values: `()`
- detail: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc1 in position 3: invalid start byte
- likely reason: Response could not be parsed against the recv definition - the command's recv types in the YAML likely don't match the real response (wrong/missing types or array-size field).
