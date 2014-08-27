__author__ = 'prikryl'
# Simple packet communication for SIRID
import socket
import logging

HEAD_LENGTH = 5
HEAD_FORMAT = "%05d"

# Pre-defined commands
AIMSUN_UP = 'AIMSUN_UP_AND_RUNNING'

class PacketCommunicator(object):

    def __init__(self, socket_instance, logger_instance):
        self.socket = socket_instance
        self.logger = logging.getLogger(logger_instance)

    def packet_receive(self):
        data_recv = None
        data = ''
        try:
            # First portion is the length as 5 digit integer
            head_len = 0
            while head_len < HEAD_LENGTH:
                data_recv = self.socket.recv(HEAD_LENGTH - head_len)
                if not data_recv:
                    break
                data += data_recv
                head_len += len(data_recv)
        except socket.error as e:
            errno, e_str = e
            self.logger.exception('exception when reading the header')
            # If Windows errno is 10054, this would be errno.ECONRESET probably
            if errno == 10054:
                self.logger.info('connection reset by peer')
                self.logger.error('errno=%d, e_str=`%s`' % (errno, e_str))
                data_recv = ''
            else:
                raise

        if not data_recv:
            self.logger.debug('no data from the socket, exiting')
            return None
        # Convert string to integer representing message length in bytes
        msg_len = int(data)
        # Announce message length
        self.logger.debug("got header announcing %d bytes from SIRID server" % msg_len)
        # Now fetch the whole string of msg_len
        data_recv = None
        data = ''
        data_len = 0
        while data_len < msg_len:
            data_recv = self.socket.recv(min(msg_len - data_len, 8192))
            if not data_recv:
                break
            data += data_recv
            data_len += len(data_recv)
        # We have to break the outer loop as well
        if not data_recv:
            self.logger.debug('no data from the socket when reading payload, exiting')
            return None
        # Announce that the message has been read
        self.logger.debug("got the whole message of %d bytes" % data_len)
        return data

    def packet_send(self, data):
        msg_str = HEAD_FORMAT % len(data)
        if len(msg_str) != HEAD_LENGTH:
            self.logger.error("inconsistent message length representation: %d instead of %d characters" %
                         (len(msg_str), HEAD_LENGTH))
            raise ValueError("Message length should be represented by %d characters, got %d" %
                             (HEAD_LENGTH, len(msg_str)))
        self.socket.sendall(msg_str)
        self.socket.sendall(data)
        # self.logger.debug("sent `%s`." % repr(msg_str + data))
