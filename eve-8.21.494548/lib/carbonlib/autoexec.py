#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\autoexec.py
import ccp_exceptions
import iocp
import _slsocket as _socket
import sys
import blue
if iocp.UsingIOCP():
    import carbonio
    select = None
    _socket.use_carbonio(True)
    carbonio._socket = _socket
    print 'Network layer using: CarbonIO'
    if iocp.LoggingCarbonIO():
        import blue
        print 'installing CarbonIO logging callbacks'
        blue.net.InstallLoggingCallbacks()
else:
    import stacklessio
    import slselect as select
    _socket.use_carbonio(False)
    stacklessio._socket = _socket
sys.modules['_socket'] = _socket
sys.modules['select'] = select
from stacklesslib import monkeypatch
monkeypatch.patch_ssl()
try:
    blue.SetCrashKeyValues(u'role', unicode(boot.role))
    blue.SetCrashKeyValues(u'build', unicode(boot.build))
    orgArgs = blue.pyos.GetArg()
    args = ''
    for each in orgArgs:
        if not each.startswith('/path'):
            args += each
            args += ' '

    blue.SetCrashKeyValues(u'startupArgs', unicode(args))
    bitCount = 32
    if blue.win32.GetNativeSystemInfo().get('ProcessorArchitecture', '') == 'PROCESSOR_ARCHITECTURE_AMD64':
        bitCount = 64
    computerInfo = {'memoryPhysical': blue.os.GlobalMemoryStatus()[1][1] / 1024,
     'cpuArchitecture': blue.pyos.GetEnv().get('PROCESSOR_ARCHITECTURE', None),
     'cpuIdentifier': blue.pyos.GetEnv().get('PROCESSOR_IDENTIFIER', None),
     'cpuLevel': int(blue.pyos.GetEnv().get('PROCESSOR_LEVEL', 0)),
     'cpuRevision': int(blue.pyos.GetEnv().get('PROCESSOR_REVISION', 0), 16),
     'cpuCount': int(blue.pyos.GetEnv().get('NUMBER_OF_PROCESSORS', 0)),
     'cpuMHz': int(round(blue.os.GetCycles()[1] / 1000.0, 1)),
     'cpuBitCount': bitCount,
     'osMajorVersion': blue.os.osMajor,
     'osMinorVersion': blue.os.osMinor,
     'osBuild': blue.os.osBuild,
     'osPatch': blue.os.osPatch,
     'osPlatform': blue.os.osPlatform}
    for key, val in computerInfo.iteritems():
        blue.SetCrashKeyValues(unicode(key), unicode(val))

except RuntimeError:
    pass

import inittools
tool = inittools.gettool()
if tool is None:
    __import__('autoexec_%s' % boot.role)
else:

    def run():
        inittools._run(tool)