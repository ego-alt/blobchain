from random import randint
import primes

"""Attempted implementation of the RSA Digital Signature Algorithm as documented by the U.S. Department of Commerce
Section B.1.1: Key Pair Generation Using Extra Random Bits
Create public and private keys for yourself"""


def bits_to_integer(bits, N):
    integer = 0
    for n in range(N):
        integer += (2 ** (N - n)) * bits[n]
    return integer


def find_prime(length, input_seed):
    finding = primes.ST_random_prime(length, input_seed)
    good_prime = finding.prime_no
    return good_prime


class PairKey:
    def __init__(self, L, N, input_seed):
        """:param L: <int> Bit length of p
        :param N: <int> Bit length of q"""

        self.p = find_prime(L, input_seed)
        self.q = find_prime(N, input_seed)
        print(self.p)
        print(self.q)

        validate = Validate()
        self.L = validate.pq(self.p, L)
        self.N = validate.pq(self.q, N)
        print(self.L)
        print(self.N)

        validate.LN(self.L, self.N)

        g = int(self.find_g(self.p, self.q))
        c = self.find_c()
        """ !-!-! validate.g() takes too damn long to run """
        validate.g(self.p, self.q, g)

        x = (c % (self.q - 1)) + 1
        y = (x ** g) % self.p
        validate.xy(x, y, self.p, self.q)

        print(x, y)

    def find_g(self, p, q):
        e = (p - 1) // q
        h = randint(1, (p - 1))
        g = (h ** e) % p
        if g == 1:
            self.find_g(p, q)
        return g

    def find_c(self):
        bitstring = [randint(0, 1) for _ in range(self.N + 64)]
        c = bits_to_integer(bitstring, self.N + 64)
        return c


class Validate:
    def __init__(self):
        pass

    def LN(self, L, N):
        min_L, min_N = 10, 5
        if L < min_L or N < min_N:
            raise Exception("(L, N) pair is INVALID")

    def pq(self, pq, ln):
        """Adjusts bit length (L, N) so that the newly generated prime numbers fall within their default relative range"
        :param pq: <int> Prime number p or q
        :param ln: Bit length of p or q respectively"""
        while not (2 ** (ln - 1) <= pq <= 2 ** ln):
            if pq < 2 ** (ln - 1):
                ln -= 1
            elif pq > 2 ** ln:
                ln += 1
        return ln

    def g(self, p, q, g):
        if not 2 <= g <= (p - 1):
            print("g is INVALID")
        if g ** q == 1 % p:
            print("g is PARTIALLY VALID")
        else:
            print("g is INVALID")

    def xy(self, x, y, p, q):
        if not 1 <= x <= (q - 1):
            print("x is INVALID")
        if not 1 <= y <= (p - 1):
            print("y is INVALID")
        else:
            print("SUCCESS")


pair = PairKey(20, 15, 927)
