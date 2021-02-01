from random import randint
from hashlib import sha256
import primes

"""Adapted the Digital Signature Algorithm as documented by the U.S. Department of Commerce
Section B.1.1: Key Pair Generation Using Extra Random Bits
Create public and private keys for yourself"""


def bits_to_integer(bits, N):
    integer = 0
    for n in range(N):
        two_power = 2 ** (N - n)
        integer += two_power * int(bits[n])
    return integer


def concatenate_binary(variables):
    f_string = ""
    for n in variables:
        n = bin(n)[2:]
        f_string = f"{f_string}{n}"
    return f_string


def find_inverse(z, a):
    if 0 < z < a:
        i, j = a, z
        y2, y1 = 0, 1
        while j > 0:
            quotient = i // j
            remainder = i - j * quotient
            y = y2 - y1 * quotient
            i, j = j, remainder
            y2, y1 = y1, y
        if i != 1:
            print("ERROR")
        else:
            return y2 % a
    else:
        print(f"{z}, {a} are INVALID")


class PairKey:
    def __init__(self, L, N, seedlen):
        """:param L: <int> Bit length of p
        :param N: <int> Bit length of q
        :param input_seed: <int> Any random number"""
        self.seedlen = seedlen
        first_seed = self.find_seed(N)

        find_q = primes.ST_random_prime(N, first_seed)
        (q_status, self.q, q_seed, q_counter) = find_q.find_prime()

        p_0 = primes.ST_random_prime(L // 2 + 1, q_seed)
        (p0_status, p0, seed, gen_counter) = p_0.find_prime()
        (p_status, self.p, p_seed, pgen_counter) = p_0.find_p(self.q, p0, L, seed, gen_counter)

        dp_seed = concatenate_binary([first_seed, p_seed, q_seed])

        self.domain_parameter_seed = bits_to_integer(dp_seed, len(dp_seed))

        validate = Validate()
        (self.L, self.N) = validate.pq(self.p, self.q, L, N)

        validate.LN(self.L, self.N)

        self.g = self.find_g(self.p, self.q, 1)
        self.c = self.find_c()

        self.x = (self.c % (self.q - 1)) + 1
        self.y = pow(self.g, self.x, self.p)
        validate.xy(self.x, self.y, self.p, self.q)

    def find_seed(self, N):
        first_seed = 0
        if self.seedlen < N:
            print("seedlen is INVALID")
        while first_seed < 2 ** (N - 1):
            first_seed = [randint(0, 1) for _ in range(self.seedlen)]
            first_seed = bits_to_integer(first_seed, self.seedlen)
        return first_seed

    def find_g(self, p, q, index):
        """:param p: <int> Prime modulus
        :param q: <int> Prime divisor of (p - 1)
        :param index: <str> Bit string of length 8
        :return g: <int> Generator of a subgroup of order q in the multiplicative group GF(p)"""
        e = (p - 1) // q
        count = 0
        g = 0
        while g < 2:
            count += 1
            ggen = 0x6767656E
            U = f"{self.domain_parameter_seed}{concatenate_binary([ggen, index, count])}"
            W = int(sha256(U.encode()).hexdigest(), 16)
            g = pow(W, e, p)
        return g

    def find_c(self):
        c = [randint(0, 1) for _ in range(self.N + 64)]
        c = bits_to_integer(c, self.N + 64)
        return c

    def find_k(self):
        c = [randint(0, 1) for _ in range(self.N + 64)]
        c = bits_to_integer(c, self.N + 64)
        k = c % (self.q - 1) + 1
        k_inv = find_inverse(k, self.q)
        return k, k_inv

    def gen_signature(self, M):
        """:param M: <str> Transaction details
        :param k: <int> Secret number unique to each message
        :param k_inv: <int> Mod q inverse of k"""
        (k, k_inv) = self.find_k()
        M = int(sha256(M.encode()).hexdigest(), 16)
        z = bin(M)[2:min(self.N, 256)]
        z = bits_to_integer(z, len(z))

        r = pow(self.g, k, self.p) % self.q
        s = (k_inv * (z + self.x * r)) % self.q
        if r == 0 or s == 0:
            self.find_k()
        return r, s

    # !-!-! verify.signature() takes too damn long to run
    def verify_signature(self, M, r, s):
        """Prior to verifying the signature, the domain parameters and public key should be available to the verifier
        :param M: <str> Received version of M (M')
        :param r: <int> Received version of r (r')
        :param s: <int> Received version of s (s')
        """
        if not (0 < r < self.q and 0 < s < self.q):
            return False
        w = find_inverse(s, self.q) % self.q
        M = int(sha256(M.encode()).hexdigest(), 16)
        z = bin(M)[2:min(self.N, 256)]
        z = bits_to_integer(z, len(z))

        u1 = (z * w) % self.q
        u2 = (r * w) % self.q
        v = ((self.g ** u1) * (self.y ** u2)) % self.p % self.q
        if v == r:
            return True


class Validate:
    def __init__(self):
        pass

    def LN(self, L, N):
        min_L, min_N = 1024, 160
        if L < min_L or N < min_N:
            raise Exception("(L, N) pair is INVALID")

    def pq(self, p, q, L, N):
        if 2 ** L <= p or 2 ** N <= q:
            print("FAILURE")
        if (p - 1) % q != 0:
            print("q is INVALID")
        return L, N

    def xy(self, x, y, p, q):
        if not 1 <= x <= (q - 1):
            print("x is INVALID")
        if not 1 <= y <= (p - 1):
            print("y is INVALID")
        else:
            print("SUCCESS")


pair = PairKey(1024, 160, 927)
(r, s) = pair.gen_signature("hello")


