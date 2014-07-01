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
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

    import java.net.Socket
    import java.io.*

    number_of_retries = 20;
    retry        = 0;
    input_socket = [];
    message      = [];

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
            input_socket.setSoTimeout(60000);

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
    
    fprintf ( 'Waiting for gantry server response ...\n' );
    
    % data_reader = DataReader(d_input_stream);
    b = 0;
    chunk = zeros(1,2048,'uint8');
    chunk_len = 0;
    while char(b) ~= '>'
        b = d_input_stream.readByte();
        chunk_len = chunk_len + 1;
        chunk(chunk_len) = b;
    end

    fprintf ( 'Got %d bytes.\n', chunk_len );

    if chunk_len == 0
        error ( ...
            'htmapi:response', ...
            'Invalid response of gantry server to `get_long_status`.' );
    end

    message = char(message'); % Data comes out as a column vector

    fprintf ( 'Got message: `%s`\n', message );
            
end
        
% ----- END ( htmSetup ) -----