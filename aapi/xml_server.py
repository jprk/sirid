__author__ = 'honza'

import socket
import time
import SocketServer

# Maximum size of a XML message. If the input buffer grows above this limit it is
# cleared and the reading starts over.
MAX_XML_SIZE = 16*1024*1024

# Buffer size. This is a chunk size
BUFFER_SIZE = 16


def process_xml_string(xml_string):
    print "--------------------------------"
    print "XML string:"
    print xml_string
    print "--------------------------------"


class RequestHandler(SocketServer.StreamRequestHandler):
    """
    The RequestHandler class for the server.

    It is instantiated once per connection to the server, and must override the
    handle() method to implement communication to the client. We make use of an
    alternative handler class that makes use of streams, which are file-like
    objects that simplify communication by providing the standard file interface.
    The server is single threaded, which means that only one client is allowed
    to connect at a time.
    """

    def handle(self):

        print "-- handler started for connection from %s" % str(self.client_address)

        # Current unprocessed data read from the request
        data = ''

        # No root tag has been found
        no_root_tag = True
        start_pos = 0
        close_pos = 0
        tag_name = None
        closing_tag = None
        look_for_eet = True

        # Infinite loop serving the requests from the SIRID hub.
        while True:

            # Sanity check: limit the buffer size
            if len(data) > MAX_XML_SIZE:
                data = ''

            # Read data from the connection, maximum BUFFER_SIZE bytes
            buff = self.request.recv(BUFFER_SIZE)
            if not buff:
                # No data from the connection means the connection has been closed
                break

            # Append the buffer to the existing data
            data += buff

            # This flag is set to False in case that we need to read another part of
            # the incoming message
            do_process_data = True

            # Loop over the contents of `data`
            while do_process_data:

                # Loop over the contents of `data` until an opening tag has been found or until the
                # buffer is exhausted and we shall read in the next part of the incoming message
                while no_root_tag:
                    # Find the first opening tag
                    open_pos = data.find('<', start_pos)
                    # Negative position signals that the string was not found. In such a care
                    # we will continue reading, which means first breaking out of the `no_root_tag`
                    # loop.
                    if open_pos == -1:
                        break
                    # We have the opening tag. What follows is according to the XML specification
                    # either '?xml ... >' or in case that the header is not present, the root element
                    # of the XML stanza.
                    # We need to isolate the whole element first
                    close_pos = data.find('>', open_pos)
                    if close_pos == -1:
                        # No closing mark yet, we will continue reading, which means first breaking
                        # out of the `no_root_tag` loop.
                        break
                    # We have isolated the opening element. The element tag name is either in the
                    # format of <root> or <root attr="val">. The suggested logic is therefore:
                    # look for the space, if found, the tag name is delimited by the space, otherwise
                    # it is limited by the closing mark
                    sp_pos = data.find(' ', open_pos)
                    if 0 <= sp_pos < close_pos:
                        # Tag format <root attr="val">
                        tag_name = data[open_pos+1:sp_pos]
                    else:
                        # Tag format <root>
                        tag_name = data[open_pos+1:close_pos]
                    if tag_name[0].isalpha():
                        # We have a root tag
                        print '   got root tag <%s>' % tag_name
                        no_root_tag = False
                    # In any case the further search will start after the closing tag of the identified
                    # element
                    start_pos = close_pos

                # End of the loop. In case that there is no opening tag, `no_root_tag` is still
                # True. In such a case we will interrupt the loop processing and continue to
                # reading the next part of the input message
                if no_root_tag:
                    # Do not search the already searched part of the buffer again
                    if open_pos == -1:
                        start_pos = len(data)
                    else:
                        start_pos = open_pos
                    # Signal the need to read another portion of the incoming message
                    do_process_data = False
                    continue
                # Now we continue looking for the closing counterpart of the opening tag. We will
                # start right after the closing > of the current tag, but before doing so we have
                # to verify that the root tag is not of the "empty-element" form <root ... />
                # The test for empty-element tag shall occur only in the first round of testing
                # right after the opening part of the tag has been identified.
                if look_for_eet:
                    if data[close_pos-1] == '/':
                        # Empty-element tag
                        process_xml_string(data[open_pos:close_pos+1])
                        # Discard the processed part of the buffer
                        data = data[close_pos+1:]
                        # And we go back to `no_root_tag`
                        no_root_tag = True
                        start_pos = 0
                        # But there might still be a payload in `data` which has not been processed,
                        # so `do_process_data` shall remain set to True
                        continue
                    else:
                        # Define what the closing tag tag is
                        closing_tag = '</'+tag_name+'>'
                        # Remember its length
                        closing_tag_len = len(closing_tag)
                        # Do not look consider empty-element tags until the next root element candidate
                        look_for_eet = False

                close_pos = data.find(closing_tag, close_pos)
                # It is not guaranteed that the current contents of `data` contains also the
                # closing tag
                if close_pos == -1:
                    # No closing tag found yet, read further on.
                    # We have to account for the possibility that a part of the closing tag has
                    # been already read (the text ends for example with '...</roo') so the
                    # position from which we continue the search is not the end of current
                    # `data` string, but it is offset by the length of the closing tag
                    close_pos = len(data)-closing_tag_len
                    if close_pos < 0:
                        close_pos = 0
                    # Signal the need to read another portion of the incoming message
                    do_process_data = False
                else:
                    # We have a closing tag
                    end_pos = close_pos+closing_tag_len
                    process_xml_string(data[open_pos:end_pos])
                    # Discard the part of `data` that corresponds to the XML message
                    data = data[end_pos:]
                    # Reset the state of the XML pre-parser: we have no root tag and the search
                    # start from the beginning of `data`
                    no_root_tag = True
                    start_pos = 0
                    look_for_eet = True
                    # The `data` string may still contain a part of the next XML message (or even
                    # a full one) and `do_process_data` shall therefore still remain set to True

            # End of the inner part of the `do_process_data loop

        # End of the receiver loop



    def finish(self):
        print "-- closing connection from %s" % str(self.client_address)
        # Force close the request socket
        SocketServer.StreamRequestHandler.finish(self)
        # Force close the request socket
        self.request.shutdown(socket.SHUT_WR)
        self.request.close()

if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 9999
    # HOST, PORT = "192.168.254.222", 9999

    # Create the multithreaded version of the server, binding to localhost on port 9999
    SERVER = SocketServer.TCPServer((HOST, PORT), RequestHandler)
    SERVER.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # server.timeout = 10
    #server.handle_request()
    print 'Server component started on %s:%d, waiting for connection.' % (HOST, PORT)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        SERVER.serve_forever()
    except:
        print 'exception occured, exitting'
        # Do not use shutdown() as this just sends message to serve_forever() which is
        # not running anymore
        # server.shutdown()
        # print 'after server.shutdown()'
time.sleep(300)