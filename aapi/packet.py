__author__ = 'prikryl'
# Simple packet communication for SIRID
import socket
import logging

logger = logging.getLogger('aapi_gantry.interface.packet')

HEAD_LENGTH = 5
HEAD_FORMAT = "%05d"

class PacketCommunicator(object):

    def __init__(self, socket_instance):
        self.socket = socket_instance

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
            logger.exception('exception when reading the header')
            # If Windows errno is 10054, this would be errno.ECONRESET probably
            if errno == 10054:
                logger.info('connection reset by peer')
                logger.error('errno=%d, e_str=`%s`' % (errno, e_str))
                data_recv = ''
            else:
                raise

        if not data_recv:
            logger.debug('no data from the socket, exiting')
            return None
        # Convert string to integer representing message length in bytes
        msg_len = int(data)
        # Announce message length
        logger.debug("got header announcing %d bytes from SIRID server" % msg_len)
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
            logger.debug('no data from the socket when reading payload, exiting')
            return None
        # Announce that the message has been read
        logger.debug("got the whole message of %d bytes" % data_len)
        return data

    def packet_send(self, data):
        msg_str = HEAD_FORMAT % len(data)
        if len(msg_str) != HEAD_LENGTH:
            logger.error("inconsistent message length representation: %d instead of %d characters" %
                         (len(msg_str), HEAD_LENGTH))
            raise ValueError("Message length should be represented by %d characters, got %d" %
                             (HEAD_LENGTH, len(msg_str)))
        self.socket.sendall(msg_str)
        self.socket.sendall(data)
        logger.debbug("sent `%s`." % repr(msg_str + data))
