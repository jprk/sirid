function ret = vgsGetSystemStatsStruct ( statFileName, aggregation )
% R=VGSGETSYSTEMSTATSSTRUCT(SFN,A) returns possibly aggregated system statistics structure
%
% @TODO@
%
% The returned structure has the following fields:
%
%   .glob ..... global statistics for the whole simulation
%   .loc  ..... periodic statistic collected in pre-selected sampling
%               intervals (usually 90 seconds, may be changed by `aggregation`
%               parameter)
%   .loc.time ... a vector of timestamps for data
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
%
%   .aggregation .... aggregation data

% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsGetSystemStatsStruct.m 2677 2010-04-27 15:32:49Z prikryl $
%

    % Check the number of arguments
    if ( nargin == 1 )
        aggregation = [];
    end
    
    % Initialise empty output
    ret = [];
    
    % Read the system statistics data from CSV
    sd = csvread ( statFileName );

    % The global data field is the last one
    sdGlobal = sd(end,:);
    if ( sdGlobal(1) ~= -1 )
        fprintf ([ ...
            'ERROR - Invalid timestamp for global system statistics data.\n' ...
            '        Expected -1, got %f\n' ], sdGlobal(1) );
        fprintf ([ ... 
            '        Ignoring the error, .glob field will be empty.\n' ]);
        % Make sure `tg` exists
        tg = [];
        % Get the number of rows representing periodical statistics
        periodRows = size ( sd, 1 );
    else
        % We really do have the global entry
        tg.flow           = sdGlobal(2);
        tg.travelTimeAvg  = sdGlobal(3);
        tg.travelTimeSdv  = sdGlobal(4);
        tg.delayTimeAvg   = sdGlobal(5);
        tg.delayTimeSdv   = sdGlobal(6);
        tg.speedAvg       = sdGlobal(7);
        tg.speedSdv       = sdGlobal(8);
        tg.density        = sdGlobal(9);
        tg.stopTimeAvg    = sdGlobal(10);
        tg.stopTimeSdv    = sdGlobal(11);
        tg.numStops       = sdGlobal(12);

        % Get the number of rows representing periodical statistics
        periodRows = size ( sd, 1 ) - 1;
    end
    
    % Distinguish between aggregation and original data: If the aggregation
    % vector is empty, we return the original data. If the vector contains
    % just a single element, we will do periodical aggregation in the
    % period given by this element. If the aggregation vector contains more
    % than one entry, we will return periodical statistics aggregated by
    % periods given by these elements.
    if ( isempty ( aggregation ))
    
        % Initialise the time vector
        tp.time           = sd(1:periodRows,1)';

        % Allocate space for all other components of the structure
        tp.flow           = zeros ( 1, periodRows );
        tp.travelTimeAvg  = zeros ( 1, periodRows );
        tp.travelTimeSdv  = zeros ( 1, periodRows );
        tp.delayTimeAvg   = zeros ( 1, periodRows );
        tp.delayTimeSdv   = zeros ( 1, periodRows );
        tp.speedAvg       = zeros ( 1, periodRows );
        tp.speedSdv       = zeros ( 1, periodRows );
        tp.density        = zeros ( 1, periodRows );
        tp.stopTimeAvg    = zeros ( 1, periodRows );
        tp.stopTimeSdv    = zeros ( 1, periodRows );
        tp.numStops       = zeros ( 1, periodRows );

        % Fill in the periodical data
        for i=1:periodRows
            tp.flow(i)           = sd(i,2);
            tp.travelTimeAvg(i)  = sd(i,3);
            tp.travelTimeSdv(i)  = sd(i,4);
            tp.delayTimeAvg(i)   = sd(i,5);
            tp.delayTimeSdv(i)   = sd(i,6);
            tp.speedAvg(i)       = sd(i,7);
            tp.speedSdv(i)       = sd(i,8);
            tp.density(i)        = sd(i,9);
            tp.stopTimeAvg(i)    = sd(i,10);
            tp.stopTimeSdv(i)    = sd(i,11);
            tp.numStops(i)       = sd(i,12);
        end
    else
        % Which type of aggregation has been specified?
        if ( length ( aggregation ) == 1 )
            
            % Determine the number of aggregated periods
            numPeriods = ceil ( sd(end-1,1) / aggregation );

            % Initialise the time vector
            tp.time = aggregation * ( 1:numPeriods );

            % Allocate space for all other components of the structure
            tp.flow           = zeros ( 1, numPeriods );
            tp.travelTimeAvg  = zeros ( 1, numPeriods );
            tp.travelTimeSdv  = zeros ( 1, numPeriods );
            tp.delayTimeAvg   = zeros ( 1, numPeriods );
            tp.delayTimeSdv   = zeros ( 1, numPeriods );
            tp.speedAvg       = zeros ( 1, numPeriods );
            tp.speedSdv       = zeros ( 1, numPeriods );
            tp.density        = zeros ( 1, numPeriods );
            tp.stopTimeAvg    = zeros ( 1, numPeriods );
            tp.stopTimeSdv    = zeros ( 1, numPeriods );
            tp.numStops       = zeros ( 1, numPeriods );
            
            % Count of aggregated data records
            agCount = 0;
            
            % Position in the aggregation array
            agPos = 1;
            
            % Fill in the periodical data
            for i=1:periodRows

                % Accumulate the statistical data into one element of the
                % aggregation vector.
                tp.flow(agPos)           = tp.flow(agPos) + sd(i,2);
                tp.travelTimeAvg(agPos)  = tp.travelTimeAvg(agPos) + sd(i,3);
                tp.travelTimeSdv(agPos)  = tp.travelTimeSdv(agPos) + sd(i,4);
                tp.delayTimeAvg(agPos)   = tp.delayTimeAvg(agPos) + sd(i,5);
                tp.delayTimeSdv(agPos)   = tp.delayTimeSdv(agPos) + sd(i,6);
                tp.speedAvg(agPos)       = tp.speedAvg(agPos) + sd(i,7);
                tp.speedSdv(agPos)       = tp.speedSdv(agPos) + sd(i,8);
                tp.density(agPos)        = tp.density(agPos) + sd(i,9);
                tp.stopTimeAvg(agPos)    = tp.stopTimeAvg(agPos) + sd(i,10);
                tp.stopTimeSdv(agPos)    = tp.stopTimeSdv(agPos) + sd(i,11);
                tp.numStops(agPos)       = tp.numStops(agPos) + sd(i,12);
                
                % Increase the count of aggregated data records
                agCount = agCount + 1;
                
                % And check the limits of the aggregation interval.
                if ( sd(i,1) > tp.time(agPos) || i == periodRows )
                    
                    % Aggregation period end. Average accumulated values.
                    tp.flow(agPos)           = tp.flow(agPos)/agCount;
                    tp.travelTimeAvg(agPos)  = tp.travelTimeAvg(agPos)/agCount;
                    tp.travelTimeSdv(agPos)  = tp.travelTimeSdv(agPos)/agCount;
                    tp.delayTimeAvg(agPos)   = tp.delayTimeAvg(agPos)/agCount;
                    tp.delayTimeSdv(agPos)   = tp.delayTimeSdv(agPos)/agCount;
                    tp.speedAvg(agPos)       = tp.speedAvg(agPos)/agCount;
                    tp.speedSdv(agPos)       = tp.speedSdv(agPos)/agCount;
                    tp.density(agPos)        = tp.density(agPos)/agCount;
                    tp.stopTimeAvg(agPos)    = tp.stopTimeAvg(agPos)/agCount;
                    tp.stopTimeSdv(agPos)    = tp.stopTimeSdv(agPos)/agCount;
                    tp.numStops(agPos)       = tp.numStops(agPos)/agCount;
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
    ret.aggregation = aggregation;
    
% ----- END ( vgsGetSystemStatsStruct ) -----