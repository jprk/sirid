function modScenario = vgsUpdateScenarioDllPath ( scenario, getramVGSdll )
% MSN=VGSUPDATESCENARIODLLPATH(SN) updates path to Getram extenstion in the scenario file. 
%
% This function searches for GetramVGS.dll or GetramVGSd.dll in
% #EXTENSIONS section of Aimsun scenario file and replaces the paths to
% these extensions with valid path on the current computer that ia given
% as a second parameter of the function.
%
% (c) 2007,2008,2009 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%         Pavel Dohnal <dohnalp@utia.cas.cz>
%
% Version: $Id: vgsUpdateScenarioDllPath.m 2739 2010-07-29 14:46:45Z prikryl $
%

    % Create filename of the temporary scenario
    tempstr = tempname();
    
    % Open the temporary file for writting
    tmp = fopen ( tempstr, 'w' );
    
    % Open the scenario file for reading
    sce = fopen ( scenario, 'r');
    
    % Copy the scenario file to the temporary location line by line,
    % changing the location of Getram extension DLL.
    is_ext = false;
    is_upd = false;
    while ~feof ( sce )
        % Read a single line from the scenario file
        tline = fgets ( sce );
        % Is the `tline` empty?
        trml = strtrim ( tline );
        if isempty ( trml ), continue; end
        % Check the beginning of the extensions section
        if ( ~is_ext )
            is_ext = ~isempty ( findstr ( tline, '#EXTENSIONS' ));
        else
            is_els3r = ~isempty( findstr ( tline, 'GetramVGS.dll' ));
            is_els3d = ~isempty( findstr ( tline, 'GetramVGSd.dll' ));
            if ( is_els3r || is_els3d )
                tline = sprintf ( '%s\n', getramVGSdll );
                is_upd = true;
            end
        end
        fwrite ( tmp, tline );
    end
    
    % Construct the extensions section if none is present
    if ~is_ext
        fprintf ( tmp, '#EXTENSIONS\n' );
    end
    
    % If the extension DLL was not found in the scenario file, inject it
    if ~is_upd
        fprintf ( tmp, '%s\n', getramVGSdll );
    end
    
    fclose ( tmp );
    fclose ( sce );
    
    % Do not rewrite the original scenario file, but move the temporary
    % file to the same directory under some meaningful name.
    [ pathstr, name, ext, versn ] = fileparts ( scenario );
    modScenario = [ pathstr filesep name 'vgs' ext versn ];
    if exist ( modScenario, 'file' )
        delete ( modScenario )
    end
    movefile ( tempstr, modScenario );
    
% ----- END ( vgsUpdateScenarioDllPath ) -----