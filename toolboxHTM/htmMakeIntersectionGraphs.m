function vgsMakeIntersectionGraphs ( statCell, titleCell, areaDescriptor, agPeriod, dirName, lang )
% VGSMAKEINTERSECTIONGRAPHS(SC,TC,NC,AP,DN,LNG) produces comparative graphs of SC by intersection.
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeIntersectionGraphs.m 2660 2010-04-02 11:35:50Z prikryl $
%

    % Number of `statCell` entries
    n = length ( statCell );
    
    % Number of intersections
    intersectionNameCell = areaDescriptor.Area.intersectionNames;
    ni = length ( intersectionNameCell );

    [ statFieldNames, ...
      statFieldDesc, ...
      statFieldYLabels, ...
      statFieldUnits ] = vgsGetLegend ( 'intersection', lang );
    
    colorMap = vgsGetColorMap ();
    
    nf = length ( statFieldNames );
    
    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\intersections\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\intersections\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\intersections\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\intersections\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    for i=1:ni
        % Name of the intersection
        in = intersectionNameCell{i};
        
        % Print the position in the section name vector
        fprintf ( '   Processing intersection ''%s'' (%d/%d) ', in, i, ni );
       
        for f=1:nf
            % Element name
            element = statFieldNames{f};
            % Clear the figure window
            clf ( fh );
            sf = strrep ( in, ' ', '_' );
            sf = strrep ( sf, '.', '_' );
            sf = strrep ( sf, '/', 'x' );
            fn = [ element '_' sf ];
            % Determine the data count
            dlen = length(statCell{1}.loc{1}.( element ));
            % Allocate data matrix for the bar graph
            data = zeros ( n, dlen);
            % Get the vector of sections that contribute to statistics of
            % this intersection
            validSections = ~isnan ( areaDescriptor.Area.intersectionMap ( i, : ));
            sections = areaDescriptor.Area.intersectionMap ( i, validSections );
            numSections = length ( sections );
            % Loop over diffetent statistics groups and accumulate
            % statistics for all sections
            for j=1:n
                % If the field name ends in `Sdv`, it contains standard
                % deviation of some quantity. In such a case we have to sum
                % squares of standard deviations (that is, variance) and
                % take a square root of the sum afterwards.
                if strcmp ( element(end-2:end), 'Sdv' )
                    for s=sections
                        data(j,:) = data(j,:) + statCell{j}.loc{s}.( element ).^2;
                    end
                    data(j,:) = sqrt ( data(j,:) );
                else
                    for s=sections
                        data(j,:) = data(j,:) + statCell{j}.loc{s}.( element );
                    end
                    if strcmp ( element, 'density' ) || strcmp ( element, 'flow' )
                        data(j,:) = data(j,:) / numSections;
                    end
                end                
            end
            % Based on the aggregation period create the time values for x axis
            c = agPeriod / 86400;
            x = c * (0:(dlen-1));
            % Plot the bar graph, returning a vector of barseries objects
            h = bar ( x, data' );
            % Set colour of every bar series
            for j=1:n
                set ( h(j), 'FaceColor', colorMap(j,:));
            end
            % X axis time format
            datetick ( 'x', 15 );
            % X limits have to be slightly below minmum and sligntly above
            % maximum in order to accomodate all barseries
            xlim ( [ min(x)-c, max(x)+c ]);
            % Title, legend, axis description
            title ( [ ...
                statFieldDesc{f}, ...
                vgsTranslate(' for intersection ',lang), ...
                in ] );
            legend ( titleCell );
            ylabel ( [ statFieldYLabels(f) statFieldUnits(f) ] );
            xlabel ( vgsTranslate('Time',lang) );
            %
            set ( fh, 'PaperUnits', 'centimeters' );
            set ( fh, 'PaperSize', [15,10] );
            set ( fh, 'PaperPositionMode', 'manual' );
            set ( fh, 'PaperPosition', [0,0,15,10] );
            %
            saveas ( fh, [ figDirPrefix 'a_' fn '.fig' ] );
            print ( fh, '-dpng', '-r200', [ pngDirPrefix 'a_' fn '.png' ] );
            print ( fh, '-dmeta', [ emfDirPrefix 'a_' fn '.emf' ] );
            vgsSaveEPS ( fh, [ epsDirPrefix 'a_' fn '.eps' ], 'windows-1250' );
            %
            fprintf ( '.' );
            %
            % An now the same for absolute differences
            %
            rdata = zeros ( n-1, dlen);
            warning ( 'off', 'MATLAB:divideByZero' );
            for j=2:n
                rdata(j-1,:) = 100 * data(j,:) ./ data(1,:) - 100;
            end
            warning ( 'on', 'MATLAB:divideByZero' );
            h = bar ( x, rdata' );
            for j=2:n
                set ( h(j-1), 'FaceColor', colorMap(j,:));
            end
            % Dotted base line
            set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
            datetick ( 'x', 15 );
            xlim ( [ min(x)-c, max(x)+c ]);
            title ( [ ...
                statFieldDesc{f}, ...
                vgsTranslate(' for intersection ',lang), ...
                in, ...
                vgsTranslate(' (relative)',lang) ...
                ] );
            legend ( titleCell{2:end} );
            ylabel ( [ ...
                statFieldYLabels{f} ...
                vgsTranslate('difference [%]',lang) ...
                ] );
            xlabel ( vgsTranslate('Time',lang) );
            %
            saveas ( fh, [ figDirPrefix 'r_' fn '.fig' ] );
            print ( fh, '-dpng', '-r200', [ pngDirPrefix 'r_' fn '.png' ] );
            print ( fh, '-dmeta', [ emfDirPrefix 'r_' fn '.emf' ] );
            vgsSaveEPS ( fh, [ epsDirPrefix 'r_' fn '.eps' ], 'windows-1250' );
            %
            fprintf ( '.' );
            %
            % An now the same for relative improvements
            %
            rdata = zeros ( n-1, dlen);
            warning ( 'off', 'MATLAB:divideByZero' );
            for j=2:n
                rdata(j-1,:) = 100 * data(j,:) ./ data(1,:) - 100;
            end
            warning ( 'on', 'MATLAB:divideByZero' );
            h = bar ( x, rdata' );
            for j=2:n
                set ( h(j-1), 'FaceColor', colorMap(j,:));
            end
            % Dotted base line
            set ( get ( h(1), 'BaseLine' ), 'LineWidth', 2, 'LineStyle', ':' );
            datetick ( 'x', 15 );
            xlim ( [ min(x)-c, max(x)+c ]);
            title ( [ ...
                statFieldDesc{f}, ...
                vgsTranslate(' for intersection ',lang), ...
                in, ...
                vgsTranslate(' (relative)',lang) ...
                ] );
            legend ( titleCell{2:end} );
            ylabel ( [ ...
                statFieldYLabels{f} ...
                vgsTranslate('difference [%]',lang) ...
                ] );
            xlabel ( vgsTranslate('Time',lang) );
            %
            saveas ( fh, [ figDirPrefix 'r_' fn '.fig' ] );
            print ( fh, '-dpng', '-r200', [ pngDirPrefix 'r_' fn '.png' ] );
            print ( fh, '-dmeta', [ emfDirPrefix 'r_' fn '.emf' ] );
            vgsSaveEPS ( fh, [ epsDirPrefix 'r_' fn '.eps' ], 'windows-1250' );
            %
            fprintf ( '.' );
            %
        end
        
        fprintf ( '\n' );
    end
    
    
% ----- END ( vgsMakeIntersectionGraphs ) -----