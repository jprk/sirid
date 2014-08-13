function netInfo = htmLoadNetworkDescription(xmlFileName)
%N=HTMLOADNETWORKDESCRIPTION(F) loads XML formatted network description for highway traffic management API.
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

%
% The following has been copied from `xmlread` documentation.
%
% ----- Local function PARSECHILDNODES -----
function children = parseChildNodes(theNode)
% Recurse over node children.
    children = [];
    if theNode.hasChildNodes
       childNodes = theNode.getChildNodes;
       numChildNodes = childNodes.getLength;
       allocCell = cell(1, numChildNodes);

       children = struct(             ...
          'Name', allocCell, 'Attributes', allocCell,    ...
          'Data', allocCell, 'Children', allocCell);

        for count = 1:numChildNodes
            theChild = childNodes.item(count-1);
            children(count) = makeStructFromNode(theChild);
        end
    end
end

%
% ----- Local function MAKESTRUCTFROMNODE -----
%
function nodeStruct = makeStructFromNode(theNode)
% Create structure of node info.

    nodeStruct = struct(                        ...
       'Name', char(theNode.getNodeName),       ...
       'Attributes', parseAttributes(theNode),  ...
       'Data', '',                              ...
       'Children', parseChildNodes(theNode));

    if any(strcmp(methods(theNode), 'getData'))
       nodeStruct.Data = char(theNode.getData); 
    else
       nodeStruct.Data = '';
    end
end

%
% ----- Local function PARSEATTRIBUTES -----
%
function attributes = parseAttributes(theNode)
% Create attributes structure.

    attributes = [];
    if theNode.hasAttributes
       theAttributes = theNode.getAttributes;
       numAttributes = theAttributes.getLength;
       allocCell = cell(1, numAttributes);
       attributes = struct('Name', allocCell, 'Value', ...
                           allocCell);

       for count = 1:numAttributes
          attrib = theAttributes.item(count-1);
          attributes(count).Name = char(attrib.getName);
          attributes(count).Value = char(attrib.getValue);
       end
    end
end

    %
    % ----- function body itself -----
    %
    % Read and parse XML data into a DOM tree
    try
        root = xmlread ( xmlFileName );
    catch
        error ( ...
            'htmapi:xmlread',...
            'Failed to read network description `%s`.', xmlFileName );
    end
    
    % Parse the DOM tree into a Matlab structure
    try
        netStruct = htmParseChildNodes ( root );
    catch
        error ( ...
            'htmapi:xmlread',...
            'Failed to read network description `%s`.', xmlFileName );
    end
    
    netInfo = struct();
    netInfo.entranceSections = [];
    netInfo.sections = [];

end
% ----- END ( htmLoadNetworkDescription ) -----
