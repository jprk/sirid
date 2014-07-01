function vgsMakeSignalGroupGraphs ( statCell, titleCell, areaDescriptor, dirName, lang )
% VGSMAKESIGNALGROUPGRAPHS(SC,TC,NC,DN,LNG) produces comparative graphs of signal groups by intersection.
%
% (c) 2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsMakeSignalGroupGraphs.m 2660 2010-04-02 11:35:50Z prikryl $
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
    
    % Massage `dirName` to end with backslash
    if dirName(end) ~= '\'
        dirName = [ dirName '\' ];
    end
    
    % Create directories
    figDirPrefix = [ dirName lang '\signalgroup\fig\' ];
    [succ,mdg,msgid] = mkdir ( figDirPrefix );
    
    pngDirPrefix = [ dirName lang '\signalgroup\png\' ];
    [succ,mdg,msgid] = mkdir ( pngDirPrefix );

    epsDirPrefix = [ dirName lang '\signalgroup\eps\' ];
    [succ,mdg,msgid] = mkdir ( epsDirPrefix );
    
    emfDirPrefix = [ dirName lang '\signalgroup\emf\' ];
    [succ,mdg,msgid] = mkdir ( emfDirPrefix );
    
    % We will need a single figure window
    fh = figure ( 'Visible', 'off' );
    
    for i=1:ni
        % Name of the intersection
        in = intersectionNameCell{i};
        
        % Make the file name
        sf = strrep ( in, ' ', '_' );
        sf = strrep ( sf, '.', '_' );
        fn = strrep ( sf, '/', 'x' );

        % Print the position in the section name vector
        fprintf ( '   Processing intersection ''%s'' (%d/%d)\n', in, i, ni );

        % Get the number of sub-graphs
        nsg = size ( statCell{1}{i}, 1 ) - 1;
    
        % Display the number of signal groups
        fprintf ( '      Intersection data contain %d signal groups.\n', nsg );
        fprintf ( '      ' );
        
        % Clear the subfigure window
        clf ( fh );

        for g=1:nsg
            % Subfigure
            ff = subplot ( nsg, 1, g );
            % Clear the subfigure window
            % clf ( ff );
            % We assume that the data range is the same for the whole set
            xdata = double(statCell{1}{i}(1,:))/86400;
            % Allocate data matrix
            ydata = zeros ( n, length(xdata));
            % Get the vectors of green lengths for the gth signal group in
            % all n experiments that are being compared.
            for c=1:n
                ydata(c,:) = statCell{c}{i}(g+1,:);
            end
            % Plot the graph, returning a vector of lineseries objects
            h = plot ( xdata, ydata );
            % Set colour of every bar series
            for j=1:n
                set ( h(j), 'Color', colorMap(j,:));
            end
            % X axis time format
            datetick ( 'x', 15 );
            % X limits have to be slightly below minmum and sligntly above
            % maximum in order to accomodate all barseries
            xlim ( [ min(xdata), max(xdata) ]);
            % Title, legend, axis description
            % title ( [ 'Signal group  for intersection ' in ] );
            % legend ( titleCell );
            % ylabel ( 'Green length [s]' );
            %
            if g == nsg 
                xlabel ( vgsTranslate ( 'Time', lang ));
            end
            %
            fprintf ( '.' );
        end
        
        % Height of the figure, 3 cm for subgraph
        ysize = 3 * nsg;
        %
        set ( fh, 'PaperUnits', 'centimeters' );
        set ( fh, 'PaperSize', [15,ysize] );
        set ( fh, 'PaperPositionMode', 'manual' );
        set ( fh, 'PaperPosition', [0,0,15,ysize] );
        %
        saveas ( fh, [ figDirPrefix 'a_' fn '.fig' ] );
        print ( fh, '-dpng', '-r200', [ pngDirPrefix 'a_' fn '.png' ] );
        print ( fh, '-dmeta', [ emfDirPrefix 'a_' fn '.emf' ] );
        vgsSaveEPS ( fh, [ epsDirPrefix 'a_' fn '.eps' ], 'windows-1250' );
        %
        fprintf ( '\n' );
    end
    
    % Close the figure
    close ( fh );
    
% ----- END ( vgsMakeSignalGroupGraphs ) -----