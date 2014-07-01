function vgsMakeSectionGraphs ( statCell, titleCell, areaDescriptor, agPeriod, dirName, lang )
% VGSMAKESECTIONGRAPHS(SC,TC,AD,AP,DN,LNG) produces comparative graphs of SC.
%
% (c) 2008,2009,2010 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeSectionGraphs.m 2721 2010-07-13 18:48:29Z prikryl $
%

    % Number of `statCell` entries
    n = length ( statCell );
    
    % Number of sections
    sectionNameCell = areaDescriptor.Area.sectionNames;
    ns = length ( sectionNameCell );

    [ statFieldNames, ...
      statFieldDesc, ...
      statFieldYLabels, ...
      statFieldUnits ] = vgsGetLegend ( 'section', lang );
    
    colorMap = vgsGetColorMap ();
    
    nf = length ( statFieldNames );
    
    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\sections\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\sections\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\sections\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\sections\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    for s=1:ns
        % Name of the section
        sn = sectionNameCell{s};
        
        % Skip elements that do not have a name
        if isempty ( sn ), continue, end;
        
        % Print the position in the section name vector
        fprintf ( '   Processing section ''%s'' (%d/%d) ', sn, s, ns );
       
        for f=1:nf
            % Element name
            element = statFieldNames{f};
            % Clear the figure window
            clf ( fh );
            sf = strrep ( sn, ' ', '_' );
            sf = strrep ( sf, '.', '_' );
            fn = [ element '_' sf ];
            % Determine the data count
            dlen = length(statCell{1}.loc{1}.( element ));
            % Allocate data matrix for the bar graph
            data = zeros ( n, dlen);
            for j=1:n
                data(j,:) = statCell{j}.loc{s}.( element );
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
            title ([ ...
                statFieldDesc{f} ...
                vgsTranslate(' for section ',lang) ...
                sn ...
                ]);
            legend ( titleCell );
            ylabel ( [ statFieldYLabels(f) statFieldUnits(f) ] );
            xlabel ( vgsTranslate('Time',lang));
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
            % An now the same for differences
            %
            rdata = zeros ( n-1, dlen);
            warning ( 'off', 'MATLAB:divideByZero' );
            for j=2:n
                rdata(j-1,:) = data(j,:) - data(1,:);
            end
            warning ( 'on', 'MATLAB:divideByZero' );
            h = bar ( x, rdata' );
            for j=2:n
                set ( h(j-1), 'FaceColor', colorMap(j,:));
            end
            datetick ( 'x', 15 );
            xlim ( [ min(x)-c, max(x)+c ]);
            title ([ ...
                statFieldDesc{f} ...
                vgsTranslate(' (whole network, relative)',lang) ...
                ]);
            legend ( titleCell{2:end} );
            ylabel ([ ...
                statFieldYLabels{f} ...
                vgsTranslate('difference',lang) ...
                ]);
            xlabel ( vgsTranslate('Time',lang));
            %
            saveas ( fh, [ figDirPrefix 'd_' fn '.fig' ] );
            print ( fh, '-dpng', '-r200', [ pngDirPrefix 'd_' fn '.png' ] );
            print ( fh, '-dmeta', [ emfDirPrefix 'd_' fn '.emf' ] );
            vgsSaveEPS ( fh, [ epsDirPrefix 'd_' fn '.eps' ], 'windows-1250' );
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
            datetick ( 'x', 15 );
            xlim ( [ min(x)-c, max(x)+c ]);
            title ([ ...
                statFieldDesc{f} ...
                vgsTranslate(' (whole network, relative)',lang) ...
                ]);
            legend ( titleCell{2:end} );
            ylabel ( [ statFieldYLabels{f} 'difference [%]' ] );
            xlabel ( vgsTranslate('Time',lang));
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
    
    
% ----- END ( vgsMakeSectionGraphs ) -----