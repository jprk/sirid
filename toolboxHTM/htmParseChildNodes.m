function children = htmParseChildNodes ( rootNode )
%C=HTMPARSECHILDNODES(R) parses DOM document in R and returns child tag hieararchy.
%
% The code is heavily inspired by `xmlread` documentation.
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
% ----- Local function MAKESTRUCTFROMNODE -----
%
function nodeStruct = makeStructFromNode(theNode)
% Create structure of node info.

    nodeStruct = struct(                        ...
       'Name', char(theNode.getNodeName),       ...
       'Attrib', parseAttributes(theNode),  ...
       'Data', '',                              ...
       'Children', htmParseChildNodes(theNode));

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

    attributes = struct();
    if theNode.hasAttributes
       theAttributes = theNode.getAttributes;
       numAttributes = theAttributes.getLength;
       for count = 1:numAttributes
          attrib = theAttributes.item(count-1);
          a_name = char(attrib.getName);
          attributes.(a_name) = char(attrib.getValue);
       end
    end
end

    % Recurse over node children.
    children = [];
    if rootNode.hasChildNodes
       childNodes = rootNode.getChildNodes;
       numChildNodes = childNodes.getLength;
       cCell = cell(1, numChildNodes);

       children = struct(             ...
          'Name', cCell, 'Attrib', struct(),    ...
          'Data', cCell, 'Children', cCell);

        for child_num = 1:numChildNodes
            theChild = childNodes.item(child_num-1);
            children(child_num) = makeStructFromNode(theChild);
        end
    end
end

