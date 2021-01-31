from hashlib import sha1
from math import gcd
from sympy import isprime

"""Generation of probable primes p and q using the Shawe-Taylor method
Implement as parameters for securely generating keys and signatures"""


def hash_int(digit):
    # Converts SHA1 hash to integer
    digit = str(digit)
    new_hash = sha1(digit.encode("utf-8")).hexdigest()
    return int(new_hash, 16)


class ST_random_prime:

    def __init__(self, length, input_seed):
        self.length = length
        self.prime_seed = input_seed
        self.prime = 0
        self.prime_gen_counter = 0
        self.outlen = 160

    def find_prime(self):
        if self.length < 2:
            return 'FAILURE', 0, 0, 0
        elif 2 <= self.length < 33:
            return self.find_c()
        else:
            return self.find_c2()

    def find_c(self):
        # Generates a pseudorandom integer c of length bits
        c = hash_int(self.prime_seed) + hash_int(self.prime_seed + 1)
        # Sets prime to the least odd integer greater than or equal to c
        while self.prime_gen_counter <= (4 * self.length) and self.prime == 0:
            c = 2 ** (self.length - 1) + c % 2 ** (self.length - 1)
            c = 2 * c // 2 + 1
            self.prime_gen_counter = self.prime_gen_counter + 1
            self.prime_seed = self.prime_seed + 2
            if isprime(c):
                self.prime = c
                return "SUCCESS", c, self.prime_seed, self.prime_gen_counter

        if self.prime_gen_counter > (4 * self.length):
            return 'FAILURE', 0, 0, 0

    def find_c2(self):
        # Generates a pseudorandom integer x in the interval [2 ** (self.length - 1), 2 ** (self.length)]
        class_object = ST_random_prime((self.length//2 + 1), self.prime_seed)
        (status, c0, self.prime_seed, self.prime_gen_counter) = class_object.find_prime()
        if status == "FAILURE":
            return 'FAILURE', 0, 0, 0

        iterations = (self.length // self.outlen) - 1
        old_counter = self.prime_gen_counter

        x = 0
        for i in range(iterations):
            x = x + hash_int(self.prime_seed + i) * (2 ** (i * self.outlen))
        self.prime_seed = self.prime_seed + iterations + 1
        x = 2 ** (self.length - 1) + x % 2 ** (self.length - 1)

        # Generates a candidate prime c in the interval [2 ** (self.length - 1), 2 ** (self.length)]
        t = x // (2 * c0)
        while self.prime_gen_counter <= (4 * self.length + old_counter):
            if 2 * t * c0 + 1 > 2 ** self.length:
                t = 2 ** (self.length - 1) // (2 * c0)
            c = 2 * t * c0 + 1
            self.prime_gen_counter = self.prime_gen_counter + 1

            a = 0
            for j in range(iterations):
                a = a + (hash_int(self.prime_seed + j) * 2 ** (j * self.outlen))
            self.prime_seed = self.prime_seed + iterations + 1
            a = 2 + a % (c - 3)
            z = pow(a, (2 * t), c)

            if 1 == gcd(z - 1, c) and 1 == pow(z, c0, c):
                self.prime = c
                return 'SUCCESS', c, self.prime_seed, self.prime_gen_counter
            t += 1

        if self.prime_gen_counter > (4 * self.length + old_counter):
            return 'FAILURE', 0, 0, 0
