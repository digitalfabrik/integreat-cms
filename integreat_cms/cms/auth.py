from django.contrib.auth.hashers import BCryptSHA256PasswordHasher


class WPBCryptPasswordHasher(BCryptSHA256PasswordHasher):
    """
    A PHP (and WordPress) compatible BCrypt password hasher that supports hashes with ``$2y$10$``.
    See https://www.php.net/manual/en/function.password-hash.php.
    For PHP style hashes only verification is supported.
    """

    algorithm: str = "bcrypt_php"
    library: tuple[str, ...] = ("bcrypt", "bcrypt")
    rounds: int = 10

    def verify(self, password: str, encoded: str) -> bool:
        """
        Validate that entered password matches stored hash

        :param password: the plain text password
        :param encoded: the hashed and salted password, i.e. from database
        :return: entered password matches the hash
        """
        bcrypt = self._load_library()
        algorithm, data = encoded.split("$", 1)
        assert algorithm == self.algorithm
        data_parts = data.split("$", 2)
        if data_parts[1] != "2y":
            return super().verify(password, encoded)
        check = bcrypt.checkpw(bytes(password, "utf-8"), bytes(data, "utf-8"))
        return check
