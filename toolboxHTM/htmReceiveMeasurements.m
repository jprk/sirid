function [res, dets] = htmReceiveMeasurements (num_messages)
% R=HTMRECEIVEMEASUREMENTS(CS) sends a control set CS to the microsimulator.
%
% Parameters:
%   num_messages ... the number of separate messages to expect
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

    function tmpb = readUntilTagFound (tmpb)
        while char(tmpb) ~= '<'
            tmpb = HTM_CONNECTION.inputstream.readByte();
        end
    end

    dets = struct();
    
    factory = javaMethod('newInstance', 'javax.xml.parsers.DocumentBuilderFactory');
    builder = factory.newDocumentBuilder();

    for gs_id = 1:num_messages
        
        document = [];
        res = 1;
        
        fprintf ( '%sReceiving message %d of %d ...\n', HTM_PREFIX, gs_id, num_messages );
    
        xml_string = htmReceiveXML('</root>');

        fprintf ( '%sParsing %d characters\n', HTM_PREFIX, length(xml_string) );
        % save ( 'xml_string.mat', 'xml_string' );
        stream = java.io.StringBufferInputStream ( xml_string );
        try
            tic;
            document = builder.parse(stream);
            elapsed = toc();
            fprintf ( '%sXML parser took %f seconds to create DOM\n', HTM_PREFIX, elapsed );
            res = 0;
        catch err
            fprintf ( '%sError parsing response!\n', HTM_PREFIX);
            res = -1;
            xml_string = '';
        end
        
        if res == 0
            fprintf ( '%sConverting DOM to struct for further manipulation\n', HTM_PREFIX );
            tic;
            root = htmParseChildNodes(document);
            elapsed = toc();
            fprintf ( '%sConversion took %f seconds\n', HTM_PREFIX, elapsed );
            
            % The top-level tag of the message always <root msg="....">
            % The msg value defines further actions
            msg_id = root.Attrib.msg;
            if strcmp ( msg_id, 'long_status' )
                fprintf ( '%sGot message "long_status" - status report with measurements\n', HTM_PREFIX );
                dets = htmProcessMeasurements(root);
                res = 0;
            elseif strcmp ( msg_id, 'simulation_finished' )
                fprintf ( '%sGot message "simulation_finished" - simulation has finished\n', HTM_PREFIX );
                res = 1;
                break;
            else
                warning ( 'htm:msgerror', 'Unknown message id `%s`', msg_id );
            end
        else
            break;
        end
    end
    
end        
% ----- END ( htmReceiveMeasurements ) -----