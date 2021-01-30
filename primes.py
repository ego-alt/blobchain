from hashlib import sha1
from math import gcd
from sympy import isprime

"""Generation of probable primes p and q using SHA1
Implement as parameters for securely generating keys and signatures"""


def hash_it(digit):
    # Converts SHA1 hash to integer
    digit = str(digit)
    new_hash = sha1(digit.encode("utf-8")).hexdigest()
    return int(new_hash, 16)


class ST_random_prime:

    def __init__(self, length, input_seed):
        self.length = (length - 1) * 2
        self.prime_seed = input_seed

        self.prime_gen_counter = 0
        self.outlen = 160
        self.iterations = (self.length // self.outlen) - 1
        self.old_counter = self.prime_gen_counter

        self.prime_no = self.find_c0()

    def find_c0(self):
        # Generates a pseudorandom integer c of length bits
        c0 = hash_it(self.prime_seed) + hash_it(self.prime_seed + 1)
        prime_no = 0
        # Sets prime to the least odd integer greater than or equal to c
        while self.prime_gen_counter <= (4 * self.length) and prime_no == 0:
            c0 = 2 ** (self.length - 1) + c0 % 2 ** (self.length - 1)
            c0 = 2 * c0 // 2 + 1
            self.prime_gen_counter = self.prime_gen_counter + 1
            self.prime_seed = self.prime_seed + 2
            if isprime(c0):
                prime_no = c0
                return prime_no
        if self.prime_gen_counter > (4 * self.length):
            print('FAILURE', 0, 0, 0)
            pass

    """ !-!-! The next half of the code takes too damn long to run """
    def find_x(self, c0):
        # Generates a pseudorandom integer x
        x = 0
        for i in range(self.iterations):
            x = x + (hash_it(self.prime_seed + i) * 2 ** (i * self.outlen))
        self.prime_seed = self.prime_seed + self.iterations + 1
        x = 2 ** (self.length - 1) + (x % 2 ** (self.length - 1))
        self.find_c(c0, x)

    def find_c(self, c0, x):
        # Generates a candidate prime c
        z, c = 0, 1
        while 1 != gcd(z - 1, c) or 1 != (z ** c0) % c:
            t = x // (2 * c0)
            if 2 * t * c0 + 1 > 2 ** self.length:
                t = 2 ** (self.length - 1) / (2 * c0)
            c = 2 * t * c0 + 1
            self.prime_gen_counter = self.prime_gen_counter + 1

            a = 0
            for j in range(self.iterations):
                a = a + (hash_it(self.prime_seed + j) * 2 ** (j * self.outlen))
            self.prime_seed = self.prime_seed + self.iterations + 1
            a = 2 + a % (c - 3)
            z = (a ** (2 * t)) % c
            t += 1

        if 1 == gcd(z - 1, c) and 1 == (z ** c0) % c:
            print('SUCCESS 2', c, self.prime_seed, self.prime_gen_counter)

        if self.prime_gen_counter > (4 * self.length + self.old_counter):
            print('FAILURE', 0, 0, 0)

