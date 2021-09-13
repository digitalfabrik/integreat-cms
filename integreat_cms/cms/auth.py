from django.contrib.auth.hashers import BCryptSHA256PasswordHasher


class WPBCryptPasswordHasher(BCryptSHA256PasswordHasher):
    """
    A PHP (and WordPress) compatible BCrypt password hasher that supports hashes with ``$2y$10$``.
    See https://www.php.net/manual/en/function.password-hash.php.
    For PHP style hashes only verification is supported.
    """

    algorithm = "bcrypt_php"
    library = ("bcrypt", "bcrypt")
    rounds = 10

    def verify(self, password, encoded):
        """
        Validate that entered password matches stored hash

        :param password: the plain text password
        :type password: str
        :param encoded: the hashed and salted password, i.e. from database
        :type encoded: str

        :return: entered password matches the hash
        :rtype: bool
        """
        bcrypt = self._load_library()
        algorithm, data = encoded.split("$", 1)
        assert algorithm == self.algorithm
        data_parts = data.split("$", 2)
        if data_parts[1] != "2y":
            return super().verify(password, encoded)
        check = bcrypt.checkpw(bytes(password, "utf-8"), bytes(data, "utf-8"))
        return check
