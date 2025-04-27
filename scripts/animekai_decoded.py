import base64
import urllib.parse
from Cryptodome.Cipher import ARC4

class KAICODEX:

    @staticmethod
    def safe_btoa(s):
        return base64.urlsafe_b64encode(s.encode("latin-1")).decode().rstrip("=")

    @staticmethod
    def safe_atob(s):
        s = s + "=" * (4 - (len(s) % 4)) if len(s) % 4 else s
        return base64.b64decode(s.replace("-", "+").replace("_", "/")).decode("latin-1")

    @staticmethod
    def homefn():
        f = [
            [0, 88], [0, 33], [0, 234], [4, 1, 7], [0, 101], [2, 188], [2, 45], [2, 74],
            [2, 232], [2, 208], [2, 124], [0, 110], [2, 211], [2, 9], [0, 153], [0, 140],
            [3, 255], [4, 6, 2], [4, 4, 4], [4, 7, 1], [4, 3, 5], [4, 4, 4], [0, 92],
            [0, 39], [0, 97], [3, 255], [0, 65], [0, 213], [0, 199], [0, 110]
        ]

        def encrypt(n):
            n = urllib.parse.quote(n)
            out = []
            fx = [
                lambda a, b: (a + b) % 256,
                lambda a, b: (a * b) & 256,
                lambda a, b: a ^ b,
                lambda a, b: ~a & b,
                lambda a, b, c: (a << b | a >> c) & 255
            ]
            for i in range(len(n)):
                fn = f[i % len(f)]
                out.append(fx[fn[0]](ord(n[i]), fn[1]) if len(fn) == 2 else fx[fn[0]](ord(n[i]), fn[1], fn[2]))
            return KAICODEX.safe_btoa(''.join(chr(code) for code in out))

        def decrypt(n):
            n = KAICODEX.safe_atob(n)
            out = []
            fx = [
                lambda a, b: (a - b + 256) % 256,
                lambda a, b: (a // b) & 256,
                lambda a, b: a ^ b,
                lambda a, b: ~a & b,
                lambda a, b, c: (a >> b | a << c) & 255
            ]
            for i in range(len(n)):
                fn = f[i % len(f)]
                out.append(fx[fn[0]](ord(n[i]), fn[1]) if len(fn) == 2 else fx[fn[0]](ord(n[i]), fn[1], fn[2]))
            return urllib.parse.unquote(''.join(chr(code) for code in out))

        return {"e": encrypt, "d": decrypt}

    @staticmethod
    def rc4(key, str_):
        cipher = ARC4.new(key.encode("latin-1"))
        encrypted = cipher.encrypt(str_.encode("latin-1"))
        return encrypted.decode("latin-1")

    @staticmethod
    def reverse_string(s):
        return s[::-1]

    @staticmethod
    def replace_chars(s, f, r):
        m = {f[i]: r[i] for i in range(len(f))}
        return ''.join(m.get(v, v) for v in s)

    @staticmethod
    def enc(n):
        return KAICODEX.homefn()['e'](n)

    @staticmethod
    def dec(n):
        return KAICODEX.homefn()['d'](n)

    @staticmethod
    def dec_mega(n):
        B = KAICODEX.safe_atob
        y = KAICODEX.rc4
        L = KAICODEX.replace_chars
        z = KAICODEX.reverse_string
        n = y('5JuOqt6PZH', B(z(L(z(L(y('gYXmZMti3aW7', B(z(L(y('VA3Y4Qj1DB', B(B(n))), 'cnifqMFatTbg', 'niMFfctgqbTa')))), 'nhdEm2PHjwO5', '5HPwnOmdhjE2')), 'bYPIshuCg3DN', '3ubICsgNhDYP'))))
        return urllib.parse.unquote(n)
