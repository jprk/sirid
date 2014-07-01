function vgsSaveEPS ( handle, filename, encoding )
% VGSSAVEEPS(H,FN,ENC) saves EPS file with given encoding vector.
%
% (c) 2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsGetLegend.m 2143 2008-08-04 06:57:55Z prikryl $
%

    % Get the name of this file and its path. We will need if for the
    % construction of the path to the encoding file.
    path = mfilename ( 'fullpath' );
    
    % Construct the name of the file with encoding
    encname = [ path '.' encoding '.enc' ];

    % Check that the encoding file exists
    if exist( encname, 'file' ) ~= 2
        error ( 'vgs:argerror', ...
            'Unknown encoding "%s" specified.', encoding );
    end
    
    % Temporary file name
    teps = [ tempname() '.eps' ];
    
    % Save the figure as the temporary EPS file 
    saveas ( handle, teps, 'epsc' );
    
    % Marker string for inserting of the new encoding vector
    mstr = '/reencode {exch dup where {pop load} {pop StandardEncoding} ifelse';

    % Open the temporary eps file
    tf = fopen ( teps, 'r' );
    
    % Open the output EPS file
    ff = fopen ( filename, 'w' );
    while true
        % Read line of the original EPS file
        line = fgetl ( tf );
        % Leave the loop if we reached EOF
        if ~ischar ( line ), break, end
        % Check our position in the input file
        if ( strcmp ( line, mstr ))
            % Include the encoding vector from the encoding file
            ef = fopen ( encname, 'r' );
            while true
                % Read line of the encoding file
                eline = fgetl ( ef );
                % Leave the loop if we reached EOF
                if ~ischar ( eline ), break, end
                % Write the line into the final EPS file
                fprintf ( ff, '%s\n', eline );
            end
            % Close the file with the encoding vector
            fclose ( ef );
        end
        % Write the original EPS line into the final EPS file
        fprintf ( ff, '%s\n', line );
    end
    % Close both files
    fclose ( tf );
    fclose ( ff );
    % Delete the temporary file
    delete ( teps );
    
% ----- END ( vgsSaveEPS ) -----