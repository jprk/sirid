function ret = vgsGetSectionStatsStruct ( statFileName, statsSectionMat, sectionLaneMap, agPeriod )
% R=VGSGETSECTIONSTATSSTRUCT(SFN,SSM,SLM,A) returns possibly aggregated section statistics structure
%
% SFN is the full path to the statistics CSV file produced by the VGS
% toolbox. SSM is a matrix of section ids holding section id aggregation
% for particular lanes or arms of the network graph - it should be part of
% the network description .mat file residing in the same directory as your
% .sce file for Aimsun. SLM is a matrix used to map queue lengths computed
% by the VGS Getram extension to queue lengths at particular lanes (the
% odd rows of the matrix hold section ids, the even rows hold lane number
% in that particular section). A is the aggregation period in seconds (use
% 3600 if you want one-hour data).
%
% The returned structure has the following fields:
%
%   .glob ..... global statistics for the whole simulation
%   .loc{} .... periodic statistic collected in pre-selected sampling
%               intervals (usually 90 seconds)
%   .loc{}.time ... a vector of timestamps for data
%   .qmax ..... a matrix of maximum queue lengths by lanes, computed in
%               GetramVGS.dll
%
%   .<both>.flow ............
%   .<both>.travelTimeAvg ...
%   .<both>.travelTimeSdv ...
%   .<both>.delayTimeAvg ....
%   .<both>.delayTimeSdv ....
%   .<both>.speedAvg ........
%   .<both>.speedSdv ........
%   .<both>.density .........
%   .<both>.stopTimeAvg .....
%   .<both>.stopTimeSdv .....
%   .<both>.numStops ........
%   .<both>.queueAvg ........
%   .<both>.queueMax ........
%
% (c) 2008,2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsGetSectionStatsStruct.m 2710 2010-07-12 09:48:18Z prikryl $
%

    % Internal function for transforming a single row of CSV data.
    %
    % `sids` is a list of section identifiers,
    % `row`  is a single row of the CSV output provided by VGS toolbox, and
    % `lmax` is the maximum number of section lanes in the network
    %        (corresponds to the maximum number of queues in a section) 
    function rcell = l_GetRowBySectionsAsCell ( sids, row, lmax )
        % Find the maximum of the sids
        maxSid = max ( sids );
        % Allocate returned cell vector
        rcell = cell ( maxSid, 1 );
        % Starting offset of the first entry
        offset = 0;
        % Loop over all sids
        for li=1:length(sids)
            % Initialise the structure
            tr = struct();
            % And build the structure
            tr.flow           = row(offset+2);
            tr.travelTimeAvg  = row(offset+3);
            tr.travelTimeSdv  = row(offset+4);
            tr.delayTimeAvg   = row(offset+5);
            tr.delayTimeSdv   = row(offset+6);
            tr.speedAvg       = row(offset+7);
            tr.speedSdv       = row(offset+8);
            tr.density        = row(offset+9);
            tr.stopTimeAvg    = row(offset+10);
            tr.stopTimeSdv    = row(offset+11);
            tr.numStops       = row(offset+12);
            tr.queueAvg       = row(offset+13);
            tr.queueMax       = row(offset+14);
            % `lmax` is at least 1 so the proper form of the range would be
            % 15:15+lmax-1.
            tr.queueLane      = row(offset+(15:14+lmax));
            % Store the section statistics
            rcell{sids(li)} = tr;
            % Advance the offset
            offset = offset + 13 + lmax;
        end
    end

    function l_E_negindex()
        error ( 'vgs:negindex', ...
            [ 'Negative queue length found. This is probably ' ...
              'due to misconfiguration of the sectionLaneMap ' ...
              'in the description of the network.' ]);
    end

    function qstats = l_CollectQueues ( lmat, rcell )
        % Size of section matrix statistics
        r = size ( lmat, 1 );
        % Preallocate returned cell vector
        qstats = zeros ( r/2, 1 );
        % Loop over all rows
        for qi = 1:2:r
            % Get the indices into `rcell` for this collection of sections.
            % The matrix holds both section and lane identifiers.
            validSections = ~isnan ( lmat ( qi,: ));
            si = lmat ( qi,   validSections );
            li = lmat ( qi+1, validSections );
            % Load the first element of the section data
            tr = rcell { si ( 1 )};
            % And initialise the queue length
            queueLane = tr.queueLane ( li ( 1 ));
            % Check if the queue length is valid
            if ( queueLane < 0 )
                %%%%%%%% l_E_negindex();
            end
            % Loop over the sections contributing to queue in this lane
            for lj = 2:length(si)
                % Select statistics data from the section
                ts = rcell { si ( lj )};
                % Fetch the queue for this lane
                qTemp = ts.queueLane ( li ( lj ));
                % Check if it is valid
                if qTemp < 0
                    %%%%%%%% l_E_negindex();
                end
                % Add the queue length in the given lane to the total
                queueLane = queueLane + qTemp;
            end
            % Store the resuld
            qstats((qi+1)/2) = queueLane;
        end
    end

    function cstats = l_CollectStats ( smat, rcell )
        % Size of section matrix statistics
        r = size ( smat, 1 );
        % Preallocate returned cell vector
        cstats = cell ( r, 1 );
        % Loop over all rows
        for li = 1:r
            % Get the indices into `rcell` for this collection of sections
            validSections = ~isnan ( smat ( li,: ));
            si = smat ( li, validSections );
            % Remember the length of the collection
            lsi = length ( si );
            % Initialise the element of the returned data set
            tr = rcell { si ( 1 )};
            tr.travelTimeSdv  = tr.travelTimeSdv^2;
            tr.delayTimeSdv   = tr.delayTimeSdv^2;
            tr.speedSdv       = tr.speedSdv^2;
            tr.stopTimeSdv    = tr.stopTimeSdv^2;
            % Loop over the rest of the collection identifiers
            for lj = 2:lsi
                % Select statistics from another section
                ts = rcell { si ( lj )};
                % Add the statistics to the result
                tr.flow           = tr.flow          + ts.flow;
                tr.travelTimeAvg  = tr.travelTimeAvg + ts.travelTimeAvg;
                tr.travelTimeSdv  = tr.travelTimeSdv + ts.travelTimeSdv^2;
                tr.delayTimeAvg   = tr.delayTimeAvg  + ts.delayTimeAvg;
                tr.delayTimeSdv   = tr.delayTimeSdv  + ts.delayTimeSdv^2;
                tr.speedAvg       = tr.speedAvg      + ts.speedAvg;
                tr.speedSdv       = tr.speedSdv      + ts.speedSdv^2;
                tr.density        = tr.density       + ts.density;
                tr.stopTimeAvg    = tr.stopTimeAvg   + ts.stopTimeAvg;
                tr.stopTimeSdv    = tr.stopTimeSdv   + ts.stopTimeSdv^2;
                tr.numStops       = tr.numStops      + ts.numStops;
                tr.queueAvg       = tr.queueAvg      + ts.queueAvg;
                tr.queueMax       = tr.queueMax      + ts.queueMax; 
            end
            % Normalize elements that shall be normalised
            tr.flow          = tr.flow / lsi;
            tr.density       = tr.density / lsi;
            tr.travelTimeSdv = sqrt ( tr.travelTimeSdv );
            tr.delayTimeSdv  = sqrt ( tr.delayTimeSdv );
            tr.speedSdv      = sqrt ( tr.speedSdv );
            tr.stopTimeSdv   = sqrt ( tr.stopTimeSdv );
            % And store it
            cstats{li} = tr;
        end
    end

    % Check the number of arguments
    if ( nargin == 3 )
        agPeriod = [];
    end
    
    % Preprocess `statsSectionMat` to sorted vector of section identifiers
    statIds = vgsGetSectionStatsIds ( statsSectionMat );

    % Get the maximal number of lanes in a section according to
    % sectionLaneMap (it will be a maximum over even rows)
    maxLanes = max ( max ( sectionLaneMap(2:2:end,:)));
    
    % Initialise empty output
    ret = [];
    
    % Read the section statistics data from CSV
    sd = csvread ( statFileName );

    % The global data field is the last one
    sdGlobal = sd(end,:);
    if ( sdGlobal(1) ~= -1 )
        fprintf ([ ...
            'ERROR - Invalid timestamp for global section statistics data.\n' ...
            '        Expected -1, got %f\n' ], sdGlobal(1) );
        fprintf ([ ...
            '        Ignoring it, just do not use the .glob part of the result.\n' ]);
        % Make sure `tg` exists
        tg = [];
        % Get the number of rows representing periodical statistics
        periodRows = size ( sd, 1 );
    else
        % Get the global statistics
        tg = l_GetRowBySectionsAsCell ( statIds, sdGlobal, maxLanes );
        % Collect particular sections
        tg = l_CollectStats ( statsSectionMat, tg );

        % Get the number of rows representing periodical statistics
        periodRows = size ( sd, 1 ) - 1;
    end
    
    % Get the number of rows of the statistics matrix.
    statRows = size ( statsSectionMat, 1 );

    % Get the number of data rows of the queue aggregation matrix.
    queueRows = size ( sectionLaneMap, 1 )/2;

    % Distinguish between aggregation and original data: If the aggregation
    % vector is empty, we return the original data. If the vector contains
    % just a single element, we will do periodical aggregation in the
    % period given by this element. If the aggregation vector contains more
    % than one entry, we will return periodical statistics aggregated by
    % periods given by these elements.
    if ( isempty ( agPeriod ))
    
        % Allocate cell array of collected section statistics.
        tp = cell ( statRows, 1 );
        
        % And initialise all cells
        for j=1:statRows
            % Initialise the time vector
            tp{j}.time           = sd(1:periodRows,1)';
            % Allocate space for all other components of the structure
            tp{j}.flow           = zeros ( 1, periodRows );
            tp{j}.travelTimeAvg  = zeros ( 1, periodRows );
            tp{j}.travelTimeSdv  = zeros ( 1, periodRows );
            tp{j}.delayTimeAvg   = zeros ( 1, periodRows );
            tp{j}.delayTimeSdv   = zeros ( 1, periodRows );
            tp{j}.speedAvg       = zeros ( 1, periodRows );
            tp{j}.speedSdv       = zeros ( 1, periodRows );
            tp{j}.density        = zeros ( 1, periodRows );
            tp{j}.stopTimeAvg    = zeros ( 1, periodRows );
            tp{j}.stopTimeSdv    = zeros ( 1, periodRows );
            tp{j}.numStops       = zeros ( 1, periodRows );
            tp{j}.queueAvg       = zeros ( 1, periodRows );
            tp{j}.queueMax       = zeros ( 1, periodRows );
        end
        
        % Create and initialise the matrix holding queue data
        tq = zeros ( queueRows, periodRows );
        
        % Fill in the periodical data
        for i=1:periodRows
            % Get the statistics for i-th time step
            tgCelS = l_GetRowBySectionsAsCell ( statIds, sd(i,:), maxLanes );
            % Collect particular sections from these statistics
            tgCell = l_CollectStats ( statsSectionMat, tgCelS );
            % And put the result into appropriate places
            for j=1:statRows
                tp{j}.flow(i)           = tgCell{j}.flow;
                tp{j}.travelTimeAvg(i)  = tgCell{j}.travelTimeAvg;
                tp{j}.travelTimeSdv(i)  = tgCell{j}.travelTimeSdv;
                tp{j}.delayTimeAvg(i)   = tgCell{j}.delayTimeAvg;
                tp{j}.delayTimeSdv(i)   = tgCell{j}.delayTimeSdv;
                tp{j}.speedAvg(i)       = tgCell{j}.speedAvg;
                tp{j}.speedSdv(i)       = tgCell{j}.speedSdv;
                tp{j}.density(i)        = tgCell{j}.density;
                tp{j}.stopTimeAvg(i)    = tgCell{j}.stopTimeAvg;
                tp{j}.stopTimeSdv(i)    = tgCell{j}.stopTimeSdv;
                tp{j}.numStops(i)       = tgCell{j}.numStops;
                tp{j}.queueAvg(i)       = tgCell{j}.queueAvg;
                tp{j}.queueMax(i)       = tgCell{j}.queueMax;
            end
            % Get the queues in this period
            tqColumn = l_CollectQueues ( sectionLaneMap, tgCelS );
            % Store them
            tq(:,i) = tqColumn;
        end
    else
        % Which type of aggregation has been specified?
        if ( length ( agPeriod ) == 1 )
            
            % Determine the number of aggregated periods
            numPeriods = ceil ( sd(periodRows,1) / agPeriod );

            % Allocate cell array of collected section statistics.
            tp = cell ( statRows, 1 );
        
            % And initialise all cells
            for j=1:statRows
                % Initialise the time vector
                tp{j}.time = agPeriod * ( 1:numPeriods );

                % Allocate space for all other components of the structure
                tp{j}.flow           = zeros ( 1, numPeriods );
                tp{j}.travelTimeAvg  = zeros ( 1, numPeriods );
                tp{j}.travelTimeSdv  = zeros ( 1, numPeriods );
                tp{j}.delayTimeAvg   = zeros ( 1, numPeriods );
                tp{j}.delayTimeSdv   = zeros ( 1, numPeriods );
                tp{j}.speedAvg       = zeros ( 1, numPeriods );
                tp{j}.speedSdv       = zeros ( 1, numPeriods );
                tp{j}.density        = zeros ( 1, numPeriods );
                tp{j}.stopTimeAvg    = zeros ( 1, numPeriods );
                tp{j}.stopTimeSdv    = zeros ( 1, numPeriods );
                tp{j}.numStops       = zeros ( 1, numPeriods );
                tp{j}.queueAvg       = zeros ( 1, numPeriods );
                tp{j}.queueMax       = zeros ( 1, numPeriods );
            end
            
            % Create and initialise the matrix holding queue data
            tq = zeros ( queueRows, numPeriods );

            % Count of aggregated data records
            agCount = 0;
            
            % Position in the aggregation array
            agPos = 1;
            
            % Pass the periodical datya
            for i=1:periodRows

                % Get the statistics for i-th time step
                tgCelS = l_GetRowBySectionsAsCell ( statIds, sd(i,:), maxLanes );
                % Collect particular sections from these statistics
                tgCell = l_CollectStats ( statsSectionMat, tgCelS );
            
                % Loop over all sections
                for j=1:statRows
                    % Accumulate the statistical data into one element of the
                    % aggregation vector.
                    tp{j}.flow(agPos)          = tp{j}.flow(agPos)          + tgCell{j}.flow;
                    tp{j}.travelTimeAvg(agPos) = tp{j}.travelTimeAvg(agPos) + tgCell{j}.travelTimeAvg;
                    tp{j}.travelTimeSdv(agPos) = tp{j}.travelTimeSdv(agPos) + tgCell{j}.travelTimeSdv;
                    tp{j}.delayTimeAvg(agPos)  = tp{j}.delayTimeAvg(agPos)  + tgCell{j}.delayTimeAvg;
                    tp{j}.delayTimeSdv(agPos)  = tp{j}.delayTimeSdv(agPos)  + tgCell{j}.delayTimeSdv;
                    tp{j}.speedAvg(agPos)      = tp{j}.speedAvg(agPos)      + tgCell{j}.speedAvg;
                    tp{j}.speedSdv(agPos)      = tp{j}.speedSdv(agPos)      + tgCell{j}.speedSdv;
                    tp{j}.density(agPos)       = tp{j}.density(agPos)       + tgCell{j}.density;
                    tp{j}.stopTimeAvg(agPos)   = tp{j}.stopTimeAvg(agPos)   + tgCell{j}.stopTimeAvg;
                    tp{j}.stopTimeSdv(agPos)   = tp{j}.stopTimeSdv(agPos)   + tgCell{j}.stopTimeSdv;
                    tp{j}.numStops(agPos)      = tp{j}.numStops(agPos)      + tgCell{j}.numStops;
                    tp{j}.queueAvg(agPos)      = tp{j}.queueAvg(agPos)      + tgCell{j}.queueAvg;
                    tp{j}.queueMax(agPos)      = tp{j}.queueMax(agPos)      + tgCell{j}.queueMax;
                end
                % Get the queues in this period
                tqColumn = l_CollectQueues ( sectionLaneMap, tgCelS );
                % Store them
                tq(:,agPos) = tq(:,agPos) + tqColumn;
                
                % Increase the count of aggregated data records
                agCount = agCount + 1;
                
                % And check the limits of the aggregation interval.
                if ( sd(i,1) > tp{1}.time(agPos) || i == periodRows )
                    
                    % Loop over all sections
                    for j=1:statRows
                        % Aggregation period end. Average accumulated values.
                        tp{j}.flow(agPos)          = tp{j}.flow(agPos)/agCount;
                        tp{j}.travelTimeAvg(agPos) = tp{j}.travelTimeAvg(agPos)/agCount;
                        tp{j}.travelTimeSdv(agPos) = tp{j}.travelTimeSdv(agPos)/agCount;
                        tp{j}.delayTimeAvg(agPos)  = tp{j}.delayTimeAvg(agPos)/agCount;
                        tp{j}.delayTimeSdv(agPos)  = tp{j}.delayTimeSdv(agPos)/agCount;
                        tp{j}.speedAvg(agPos)      = tp{j}.speedAvg(agPos)/agCount;
                        tp{j}.speedSdv(agPos)      = tp{j}.speedSdv(agPos)/agCount;
                        tp{j}.density(agPos)       = tp{j}.density(agPos)/agCount;
                        tp{j}.stopTimeAvg(agPos)   = tp{j}.stopTimeAvg(agPos)/agCount;
                        tp{j}.stopTimeSdv(agPos)   = tp{j}.stopTimeSdv(agPos)/agCount;
                        tp{j}.numStops(agPos)      = tp{j}.numStops(agPos)/agCount;
                        tp{j}.queueAvg(agPos)      = tp{j}.queueAvg(agPos)/agCount;
                        tp{j}.queueMax(agPos)      = tp{j}.queueMax(agPos)/agCount;
                    end
                    % And process also the maximul queue length
                    tq(:,agPos) = tq(:,agPos)/agCount;
                    
                    % Reset the count
                    agCount = 0;
                    
                    % Move to the next aggregation vector element
                    agPos = agPos + 1;
                end
            end
        else
            error ( 'Variable period aggregation not implemented yet.' );
        end
    end
    
    % And put together the returned structure
    ret.glob = tg;
    ret.loc  = tp;
    ret.qmax = tq;

end    
% ----- END ( vgsGetSectionStatsStruct ) -----