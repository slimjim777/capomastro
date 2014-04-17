from django.test import TestCase

import mock

from credentials.models import SshKeyPair


class SshKeyPairTest(TestCase):

    public_key = """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTx+Q1k+3Rej6giYUQtZ9rgqqz0/crkyVaKOUL1h/lr6ORmjAABy6iCVDY1jvIBHv2//a7eOW/Na86p6UtYO+vHF5S0EC+Fl6pQoXmAiPVp6MqyA8psj2b6YaNW9CKmp2OtzFvpmnzQxYfafBejlNIKhfHofW7e9UjL2FVzlAgnNeDv8u2K1bPFO7ikiwYdMmNPDvYK82N9+JXo8OCma03Rvav5juJg1Ldzw1sMvYWTI41ccFlDxP3W/lQAnXVaERqVV1rX33hfJh3cjCHltV3D1V0/rV/U2d/Vc5/IM6hb0I/hsvqv6cLzaWSE5HTZh9GWU9Uhx/ZMCAk6wmZjwZ/ test@test"""
    private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA08fkNZPt0Xo+oImFELWfa4Kqs9P3K5MlWijlC9Yf5a+jkZow
AAcuoglQ2NY7yAR79v/2u3jlvzWvOqelLWDvrxxeUtBAvhZeqUKF5gIj1aejKsgP
KbI9m+mGjVvQipqdjrcxb6Zp80MWH2nwXo5TSCoXx6H1u3vVIy9hVc5QIJzXg7/L
titWzxTu4pIsGHTJjTw72CvNjffiV6PDgpmtN0b2r+Y7iYNS3c8NbDL2FkyONXHB
ZQ8T91v5UAJ11WhEalVda1994XyYd3Iwh5bVdw9VdP61f1Nnf1XOfyDOoW9CP4bL
6r+nC82lkhOR02YfRllPVIcf2TAgJOsJmY8GfwIDAQABAoIBAEdzdmQ5L5BwPPbu
zs0vacTdBfi79/VkpMKBb52JtaNJmdcC/VTVF3+lwvgVd3/pO2W/QCBKDsFvPFp+
uzTPMq6S1KP+DQnVBET447IRYMOx1lQVwT/hGfYjWLkSlA5fUe8XkX9I1xAyvyEE
HgvY2vJK+VDqLLz/b456as2HWPNXOiOyk0HiD9deVcRHSG+wXLR33OA6ADxkeJvu
OnDKEsLMPrGIuMFP9V9PloIwdfxI4G3VRrydIlmJAX+6g9Q0gHD0zeUHClHQk7OL
0ujpc95u1gsvruy4FMhv/YK6+bWLttR5oqoSLpPC8doU84641TE9ox+mgEPsuCF8
EcYGGRECgYEA6ttOeF4vdLvrPuGhNqv9KmbnpyfVJ3LFqmWpaGHuuiH4OznH+AUP
xTOy3tU01IdUA0Vgh3vY1hB/ofkUheFkqDU4GZaEYMo4XaXFJGrnUWkM8UUeApbf
Kaop0Ky2dKcPgSEsuZxEH2do2RVoGm/nKzZM/jze8SgVpiOdgiFNGecCgYEA5tjC
wPhPx7T2bi0Kg7eNdvbyZVV/04Wfweo788tSHf4a8zNAMgLZ5P5r0TRlLzNDd4lW
7jFGRxZBt5/2hY4Z5t5MzkVcDZ/aTwhgLRDiLAF5TY1Hus+keC33OzwO/xLSXyfF
WeV74Zp9EhTsDWV1qzmXfbXissSitrG/moyUC6kCgYEA1KgLn7Y45kyaMHABmA2X
yWMwcw0AVx33mdk/0kKK9YN4z7f8N7ntk7TCTD9l/OMk0WlqhINBzmNWDoYJbUiv
6hd2WsUNzM6Ox00o+1bJac/jZjwddl7CZ2mrP0aEV5BF27j8VH0Iuh7as2ZMw1N8
UIZ0pOjdPiP7plotbv1UYRUCgYBb8P0wSjXMPoDfxMSpTVPki9pjDbiJkHDelOIn
6VTdaTVmo4Tv5j7Oe56Jhiq+r9YxJ9wdpjZtXany7p0K+FvMncFNbkaJjp8uVxGn
IVBTYorjnl9xQf4pd3U+fF8krGRpTbfGZCYA5rzllLunYj+JYLi7ctPFi5ea2BSO
A2t7cQKBgQDdXFNCgAcSx73nfTPcGM6NYuVk2muRwbEEEv7rqg0GYa0wG9vy/cf7
iaOqPsc2hLDQoWIoTNZVd190N/ssl+1b+HybqpzKSJME1X06yjEMcBlSHXZRt5wF
mzqe8/sSG//s7IsTTwmZLP87A5vv59SXZZzwiyENSEJ+0PE5bNXEww==
-----END RSA PRIVATE KEY-----
"""

    def test_get_pkey(self):
        """
        get_pkey should return an RSAKey loaded with the
        public and private key.
        """
        with mock.patch("credentials.models.RSAKey") as mock_key:
            keypair = SshKeyPair(
                label="testing key", public_key=self.public_key,
                private_key=self.private_key)
            keypair.get_pkey()
        self.assertEqual(
            self.private_key, mock_key.call_args[1]["file_obj"].read())
        self.assertEqual(
            self.public_key, mock_key.call_args[1]["data"])
