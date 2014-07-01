function data = vgsAggregateSections ( secCell, element, areaDescriptor, matchPos )
% D=VGSAGGREGATESECTIONS(SC,E,AD,POS) aggregates information from seciton cell vector.
%
% Parameters:
%   secCell .......... aggreghated statisticla data for all sections in
%                      the network
%   element .......... statistical element that should be aggregated
%   areaDescriptor ... description of the network we were simulating
%   matchPos ......... position of the output type in the area aggregation
%                      maps
%
% (c) 2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsAggregateSections.m 2385 2009-05-17 23:02:02Z prikryl $
%

    % Number of `statCell` entries
    n = length ( secCell );

    % Determine the data count
    dlen = length ( secCell{1}.loc{1}.( element ));

    % Allocate data matrix
    data = zeros ( n, dlen );

    % Get the vector of sections that contribute to statistics of
    % this intersection
    validSections = ~isnan ( areaDescriptor.Area.aggregationInfo.sectionMap ( matchPos, : ));
    sections = areaDescriptor.Area.aggregationInfo.sectionMap ( matchPos, validSections );
    numSections = length ( sections );
    
    % Loop over different statistics groups and accumulate
    % statistics for all sections
    for j=1:n
        % If the field name ends in `Sdv`, it contains standard
        % deviation of some quantity. In such a case we have to sum
        % squares of standard deviations (that is, variance) and
        % take a square root of the sum afterwards.
        if strcmp ( element(end-2:end), 'Sdv' )
            for s=sections
                data(j,:) = data(j,:) + secCell{j}.loc{s}.( element ).^2;
            end
            data(j,:) = sqrt ( data(j,:) );
        else
            for s=sections
                data(j,:) = data(j,:) + secCell{j}.loc{s}.( element );
            end
            if strcmp ( element, 'density' ) || strcmp ( element, 'flow' )
                data(j,:) = data(j,:) / numSections;
            end
        end                
    end

% ----- END ( vgsAggregateSections ) -----
