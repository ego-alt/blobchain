from random import choice, randint
import primes


def find_primes(min, max):
    prime_list = []
    for n in range(0, max - 31, 30):
        for i in [7 + n, 11 + n, 13 + n, 17 + n, 19 + n, 23 + n, 29 + n, 31 + n]:
            if i in range(min, max - 1):
                prime_list.append(i)
    return prime_list


def bits_to_integer(bits, N):
    integer = 0
    for n in range(N):
        integer += (2 ** (N - n)) * bits[n]
    return integer


class PairKey:
    def __init__(self, L, N, seedlen):
        """:param L: <int> Bit length of p
        :param N: <int> Bit length of q"""
        self.L = L
        self.N = N

        self.seedlen = seedlen
        first_seed = self.find_firstseed()

        validate = Validate()
        validate.LN(self.L, self.N, self.seedlen)

        p = int(self.find_p())
        q = int(self.find_q(p))
        g = int(self.find_g(p, q))
        c = self.find_c()

        validate.g(p, q, g)

        x = (c % (q - 1)) + 1
        y = (x ** g) % p
        validate.xy(x, y, p, q)

        print(x, y)

    def find_firstseed(self):
        firstseed = ''.join(randint(0, 1) for _ in range(2 ** (self.N - 1)))
        return firstseed

    def find_p(self):
        p = find_primes(2 ** (self.L - 1), 2 ** self.L)
        p_prime = choice(p)
        return p_prime

    def find_q(self, p):
        q = [i for i in find_primes(p2 ** (self.N - 1), 2 ** self.N) if (p - 1) % i != 0]
        q_prime = choice(q)
        return q_prime

    def find_g(self, p, q):
        e = (p - 1) / q
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

    def LN(self, L, N, seedlen):
        min_L, min_N = 10, 5
        if L < min_L or N < min_N:
            raise Exception("(L, N) pair is INVALID")
        if seedlen < N:
            raise Exception("Seedlength is INVALID")

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


pair = PairKey(20, 15)
