function payload = htmReceiveXML(closing_tag)
% XML=HTMRECEIVEXML(C) reveives a block of XML data with a closing tag C
%
% The received XML block is expected in the format
% <?xml ...> tags ... closing_tag
%
% The closing tag has to be specified in full, i.e. </root>
%
% Parameters:
%   closing_tag ... the closing tag of the XML entity
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

global HTM_CONNECTION;
global HTM_PREFIX;

    import java.net.Socket
    import java.io.*

    function tmpb = readUntilTagFound (tmpb)
        while char(tmpb) ~= '<'
            tmpb = HTM_CONNECTION.inputstream.readByte();
        end
    end

    res = 1;

    fprintf ( '%sWaiting for gantry server response ...\n', HTM_PREFIX );

    % We assume that the incoming XML is well formed, that is it begins
    % with a valid XML header '<?...?>. So the first part of the reveiver
    % routine waits for this header and ignore everything else
    tic;
    b2 = 0;
    have_header = false;
    while ~have_header
        b1 = readUntilTagFound(b2);
        b2 = HTM_CONNECTION.inputstream.readByte();
        prefix = char([b1 b2]);
        if strcmp(prefix,'<?')
            have_header = true;
        end
    end
    elapsed = toc();
    fprintf ( '%sGot xml header in %f seconds\n', HTM_PREFIX, elapsed );

    % Now we have found the beginning of a XML stanza sent to us by the
    % server. We will read everything until closing </root> tag which is
    % bound to be there as well.
    tic;
    payload = '';
    chunk = zeros(1,2048,'uint8');
    chunk(1:2) = [b1 b2];
    chunk_len = 2;
    do_read = true;
    b = b2;
    while do_read
        while char(b) ~= '>'
            b = HTM_CONNECTION.inputstream.readByte();
            chunk_len = chunk_len + 1;
            chunk(chunk_len) = b;
        end
        % This is a XML tag isolated from the input stream
        xmltag = strtrim(char(chunk(1:chunk_len)));
        payload = [ payload xmltag ];
        if strcmp(xmltag, closing_tag)
            break;
        else
            % Read and store everything that precedes the next opening XML
            % tag
            chunk_len = 0;
            while char(b) ~= '<'
                b = HTM_CONNECTION.inputstream.readByte();
                chunk_len = chunk_len + 1;
                chunk(chunk_len) = b;
            end
            % This is the text between closing an opening XML tags
            text = strtrim(char(chunk(1:chunk_len-1)));
            payload = [ payload text ];
            chunk(1) = b;
            chunk_len = 1;
        end
    end

    elapsed = toc();
    fprintf ( '%sReading the message took %f seconds\n', HTM_PREFIX, elapsed );
    
end        
% ----- END ( htmReceiveMeasurements ) -----