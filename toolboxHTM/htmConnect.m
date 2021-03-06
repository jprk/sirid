function htmConnect ( host, port )
% R=HTMCONNECT(H,P) connects to a gantry server running at host H port P.
%
% Parameters:
%   host ... FQDN of the server
%   port ... port number where the gantry server accepts connections
%
% See also
% http://iheartmatlab.blogspot.cz/2009/09/tcpip-socket-communications-in-matlab.html
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 �VUT FD 
%
% Author: Jan P�ikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

global HTM_CONNECTION;

    import java.net.Socket
    import java.io.*

    number_of_retries = 20;
    retry        = 0;
    input_socket = [];

    while true

        retry = retry + 1;
        if ((number_of_retries > 0) && (retry > number_of_retries))
            error ( ...
                'htmapi:connect', ...
                'Cannot connect to gantry server at %s:%d - too many retires.', ...
                host, port );
        end
        
        try
            fprintf(1, 'Retry %d connecting to %s:%d\n', retry, host, port);

            % throws if unable to connect
            input_socket = Socket(host, port);
            
            fprintf(1, 'Connected to server\n');

            % Set a timeout to the operations on this socket
            input_socket.setSoTimeout(120000);

            fprintf(1, 'Set timeout\n');

            % get a buffered data input stream from the socket
            input_stream   = input_socket.getInputStream;
            d_input_stream = DataInputStream(input_stream);

            % get a buffered data output stream from the socket
            output_stream   = input_socket.getOutputStream;
            d_output_stream = DataOutputStream(output_stream);

            fprintf(1, 'Got streams\n');

            % Send first heartbeat message. The message flag `synchronise`
            % is set to `true` which means that as soon as the server
            % started the simulation we will get a ping back.
            htmSendGetLongStatus ( d_output_stream, true );
            
            break;
            
        catch err
            if ~isempty(input_socket)
                input_socket.close;
            end
            
            err
            err.message
            err.stack
            
            % pause before retrying
            pause(1);
        end
    end
        
    %
    
    HTM_CONNECTION.inputstream = d_input_stream;
    HTM_CONNECTION.outputstream = d_output_stream;
            
    fprintf ( 'Waiting for gantry server response ...\n' );
    
    xml_string = htmReceiveXML('</root>');
    msg_len = length(xml_string);
    
    fprintf ( 'Got %d bytes.\n', msg_len);

    if msg_len == 0
        error ( ...
            'htmapi:response', ...
            'Invalid response of gantry server to `get_long_status`.' );
    end

    fprintf ( 'Got message: `%s`\n', xml_string );
    
end
        
% ----- END ( htmConnect ) -----