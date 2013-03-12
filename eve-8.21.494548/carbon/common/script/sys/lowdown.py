#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/common/script/sys/lowdown.py
from blue.crypto import *
import blue
import blue.win32
import util
import cPickle
import cStringIO
import os
goldName = 'root:/GoldenCD.pikl'
nullmanifestName = 'root:/manifest.dat'
bluekeyName = 'root:/../carbon/src/blue/bluekey.h'

def TmpContext():
    return CryptAcquireContext(None, MS_ENHANCED_PROV, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)


def KeyFromPassword(c, pw):
    hash = CryptCreateHash(c, CALG_SHA, None, 0)
    CryptHashData(hash, pw, 0)
    key = CryptDeriveKey(c, CALG_RC4, hash, 0)
    return key


def ImportPlainSessionBlob(c, blob):
    pKey = CryptGenPrivateExponentOneKey(c, AT_KEYEXCHANGE)
    return CryptImportKey(c, blob, pKey, 0)


def ExportPlainSessionBlob(c, sessionKey):
    pKey = CryptGenPrivateExponentOneKey(c, AT_KEYEXCHANGE)
    return CryptExportKey(sessionKey, pKey, SIMPLEBLOB, 0)


def Test():
    c = TmpContext()
    siglen = 1024
    sig = CryptGenKey(c, AT_SIGNATURE, siglen << 16 | CRYPT_EXPORTABLE)
    public = CryptExportKey(sig, None, PUBLICKEYBLOB, 0)
    private = CryptExportKey(sig, None, PRIVATEKEYBLOB, 0)
    cryptlen = 128
    cryptKey = CryptGenKey(c, CALG_RC4, cryptlen << 16 | CRYPT_EXPORTABLE)
    crypt = CryptExportKey(cryptKey, None, PLAINTEXTKEYBLOB, 0)
    text = 'rafmagnsbassi'
    ct = CryptEncrypt(cryptKey, None, True, 0, text)
    cropt = ExportPlainSessionBlob(c, cryptKey)
    c = TmpContext()
    cryptKey = ImportPlainSessionBlob(c, cropt)
    pt = CryptDecrypt(cryptKey, None, True, 0, ct)
    print [ct, pt]
    return (crypt, cropt)


def GenCodeAccessor(pw, goldName = 'GoldenCD.pikl', bluekeyName = 'bluekey.h'):
    c = TmpContext()
    timeStamp = util.FmtDateEng(blue.os.GetWallclockTime())
    pwkey = KeyFromPassword(c, pw)
    siglen = 1024
    sig = CryptGenKey(c, AT_SIGNATURE, siglen << 16 | CRYPT_EXPORTABLE)
    public = CryptExportKey(sig, None, PUBLICKEYBLOB, 0)
    private = CryptExportKey(sig, pwkey, PRIVATEKEYBLOB, 0)
    cryptlen = 168
    crypt = CryptGenKey(c, CALG_3DES, cryptlen << 16 | CRYPT_EXPORTABLE)
    crypt = ExportPlainSessionBlob(c, crypt)
    f = file(bluekeyName, 'w')
    WriteBlueSrc(f, timeStamp, public, crypt)
    f.close()
    gold = {'timeStamp': timeStamp,
     'codeSignaturePublic': public,
     'codeSignaturePrivate': private,
     'codeEncryption': crypt,
     'date': util.FmtDateEng(blue.os.GetWallclockTime())}
    f = file(goldName, 'w')
    cPickle.dump(gold, f)
    f.close()


def ChangePassword(pw, newpw, goldName = goldName):
    goldName = blue.paths.ResolvePath(goldName)
    c = TmpContext()
    pwkey = KeyFromPassword(c, pw)
    f = file(goldName, 'r')
    gold = cPickle.load(f)
    f.close()
    private = CryptImportKey(c, gold['codeSignaturePrivate'], pwkey, CRYPT_EXPORTABLE)
    pwkey = KeyFromPassword(c, newpw)
    gold['codeSignaturePrivate'] = CryptExportKey(private, pwkey, PRIVATEKEYBLOB, 0)
    f = file(goldName, 'w')
    cPickle.dump(gold, f)
    f.close()
    print 'changed password of %r from %r to %r' % (goldName, pw, newpw)


def CheckPassword(pw, goldName = goldName):
    goldName = blue.paths.ResolvePath(goldName)
    c = TmpContext()
    pwkey = KeyFromPassword(c, pw)
    f = file(goldName, 'r')
    gold = cPickle.load(f)
    f.close()
    try:
        private = CryptImportKey(c, gold['codeSignaturePrivate'], pwkey, CRYPT_EXPORTABLE)
    except blue.win32.NTE_BAD_DATA:
        return False

    return True


def WriteBlueSrc(f, timeStamp, pubblob, cryptblob):
    print >> f, '/*This file is autogenerated by python at %s */' % timeStamp
    print >> f, 'const char codeSigKey[] = {'
    WriteChars(f, pubblob)
    print >> f, '};\n'
    print >> f, 'const char codeCryptKey[] = {'
    WriteChars(f, cryptblob)
    print >> f, '};'
    print >> f, 'const char codeTimeStamp[] = "%s";' % timeStamp


def WriteChars(f, string):
    while string:
        bit = string[:10]
        string = string[10:]
        for c in bit:
            print >> f, "'\\x%s', " % hex(ord(c))[2:],

        print >> f, ''


def CreateBinManifestSource(path, head, subst):
    lines = []
    for dir in os.walk(path, False):
        for f in dir[2]:
            lines.append(os.path.join(dir[0], f))

        lines.append('-' + dir[0] + '/')

    for i, orgline in enumerate(lines):
        line = orgline.replace(head, subst, 1)
        line = line.replace('\\', '/')
        while '//' in line:
            line = line.replace('//', '/')

        if not orgline.startswith('-'):
            lines[i] = ' '.join((orgline, line))
        else:
            lines[i] = line
        lines[i] = lines[i].encode('utf8')

    return cStringIO.StringIO('\n'.join(lines))


def CreateManifest(listNames, goldName, manifestName, pw):
    c = TmpContext()
    pwkey = KeyFromPassword(c, pw)
    f = file(blue.paths.ResolvePath(goldName), 'r')
    gold = cPickle.load(f)
    f.close()
    priv = CryptImportKey(c, gold['codeSignaturePrivate'], pwkey, 0)
    log = manifestName + '.log'
    log = blue.paths.ResolvePathForWriting(log)
    log = file(log, 'w')
    print >> log, 'Manifest log '
    files = []
    for listName in listNames:
        if hasattr(listName, 'read'):
            f = listName
        else:
            f = file(blue.paths.ResolvePath(listName), 'r')
        for line in f:
            line = line.decode('utf8').strip()
            if u'#' in line:
                line = line[0:line.find(u'#')]
            if not line:
                continue
            if line.startswith(u'!'):
                files.append(line[1:])
            else:
                files.append(line.split())

    manifest = []
    seenFiles = set()
    for f in files:
        print f
        if type(f) is unicode:
            manifest.append(f.encode('utf8'))
            print >> log, 'directive: %r' % f
        elif len(f) == 1 and len(f[0]) >= 2 and f[0][0] == u'-' and f[0][-1] == u'/':
            f = f[0][1:]
            manifest.append((f.encode('utf8'), '', 0))
            print >> log, 'dir exclude %r' % f
        else:
            if len(f) == 1:
                f.append(f[0])
            if f[1].lower() in seenFiles:
                continue
            seenFiles.add(f[1].lower())
            sp0 = os.path.split(f[0])
            sp1 = os.path.split(f[1])
            if sp0[1].lower() == sp1[1].lower():
                rf = os.path.split(GetRealCase(blue.paths.ResolvePath(f[0])))[1]
                if rf != sp1[1]:
                    print 'replaced target file case from %r to %r' % (sp1[1], rf)
                    f[0] = os.path.join(sp0[0], rf)
                    f[1] = os.path.join(sp1[0], rf)
            hash = SignFile(f[0], c)
            crc = Crc32File(f[0])
            manifest.append((f[1].encode('utf8'), hash, crc))
            print >> log, '%r crc:%r, hash:%r' % (f[1], hex(crc & 4294967295L), hash)
        print manifest[-1]

    manifest = PackManifest(manifest, gold['timeStamp'], c, CALG_SHA)
    f = file(blue.paths.ResolvePathForWriting(manifestName), 'wb')
    f.write(manifest)
    f.close()
    print >> log, '%s files with keys from %s done' % (len(files), gold['timeStamp'])
    log.close()


def GetRealCase(filename):
    path, base = os.path.split(filename)
    files = os.listdir(path)
    try:
        i = [ f.lower() for f in files ].index(base.lower())
    except ValueError:
        raise IOError, filename + ' not found'

    return os.path.join(path, files[i])


def SignFile(fn, c):
    full = blue.paths.ResolvePath(fn)
    f = file(full, 'rb')
    data = f.read()
    f.close()
    hash = CryptCreateHash(c, CALG_SHA, None, 0)
    CryptHashData(hash, data, 0)
    sign = CryptSignHash(hash, AT_SIGNATURE, 0)
    return sign


def SignData(data, privateKey = None, password = None):
    if privateKey == None:
        f = file(blue.paths.ResolvePath(goldName), 'r')
        gold = cPickle.load(f)
        f.close()
        privateKey = gold['codeSignaturePrivate']
    if password == None:
        import nt
        password = nt.environ.get('signaturepwd', '')
    ctx = CryptAcquireContext(None, MS_ENHANCED_PROV, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)
    passwordkey = KeyFromPassword(ctx, password)
    blue.crypto.CryptImportKey(ctx, privateKey, passwordkey, 0)
    hash = CryptCreateHash(ctx, CALG_SHA, None, 0)
    CryptHashData(hash, data, 0)
    sign = CryptSignHash(hash, AT_SIGNATURE, 0)
    hash.Destroy()
    return sign


def VerifyDataSignature(data, signature):
    ctx = blue.crypto.GetVerContext()
    hash = CryptCreateHash(ctx, CALG_SHA, None, 0)
    CryptHashData(hash, data)
    pKey = blue.crypto.GetVerKey()
    valid = CryptVerifySignature(hash, signature, pKey)
    hash.Destroy()
    return valid


def Crc32File(fn):
    full = blue.paths.ResolvePath(fn)
    f = file(full, 'rb')
    data = f.read()
    f.close()
    return Crc32(data)


def VerifyManifestFile(fn):
    return blue.crypto.VerifyManifestFile(fn)


def CNM(pw, goldName = goldName, nullmanifestName = nullmanifestName):
    mf = '!greetings, programmer!\n'
    mf = cStringIO.StringIO(mf)
    goldName = blue.paths.ResolvePath(goldName)
    nullmanifestName = blue.paths.ResolvePath(nullmanifestName)
    CreateManifest([mf], goldName, nullmanifestName, pw)


def NewAccessor(pw, goldName = goldName, nullmanifestName = nullmanifestName, bluekeyName = bluekeyName):
    if not ValidateAccessorString(pw):
        raise RuntimeError('Given accessor contains invalid characters! Choose another.')
    goldName = blue.paths.ResolvePath(goldName)
    nullmanifestName = blue.paths.ResolvePath(nullmanifestName)
    bluekeyName = blue.paths.ResolvePath(bluekeyName)
    GenCodeAccessor(pw, goldName, bluekeyName)
    CNM(pw, goldName, nullmanifestName)


def ValidateAccessorString(pw):
    invalid = '\\/:*?"<>|&\''
    string = pw
    for char in invalid:
        if char in string:
            print 'Found "{0}" in accessor!'.format(char)
            string = string.replace(char, '')

    return string == pw


exports = {'lowdown.GenCodeAccessor': GenCodeAccessor,
 'lowdown.ChangePassword': ChangePassword,
 'lowdown.CheckPassword': CheckPassword,
 'lowdown.CreateBinManifestSource': CreateBinManifestSource,
 'lowdown.CreateManifest': CreateManifest,
 'lowdown.VerifyManifestFile': VerifyManifestFile,
 'lowdown.Test': Test,
 'lowdown.NewAccessor': NewAccessor,
 'lowdown.ValidateAccessorString': ValidateAccessorString,
 'lowdown.SignData': SignData,
 'lowdown.VerifyDataSignature': VerifyDataSignature,
 'lowdown.CNM': CNM}