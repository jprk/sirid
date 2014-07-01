function ret = htmInit ( archStr, isDebugging )
% R=VGSINIT() initialises vgs_api DLL
%
% Unloads the library if it has been already loaded.
% Returns TRUE if the library has been loaded sucessfuly, FALSE otherwise.
%
% (c) 2008,2013 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsInit.m 3091 2013-08-21 16:29:51Z prikryl $
%

    % If the library has been loaded already, get rid of it.
    htmUnload ();

    % Check the number of function parameters
    if nargin < 2
        isDebugging = 0;
    end

    % Make the DLL acessible to Matlab
    library = 'htm_api.dll';
    if isDebugging
        library = 'htm_apid.dll';
    end
    
    % We need a full path to the header file directory. A relative path
    % would work only in case when the working directory is the toolbox
    % directory - and we do not want to have this.
    thisFile  = mfilename ( 'fullpath' );
    % This worked in Matlab 7 but generates an error in 2012a and later
    % [ thisPath, name, ext, ver ]  = fileparts ( thisFile );
    thisPath = fileparts ( thisFile );
    
    % Make the DLL acessible to Matlab
    loadlibrary ( ...
        fullfile ( thisPath, archStr, library ), ...
        fullfile ( thisPath, 'headers', 'htmapi.h' ), ...
        'alias', 'htm_api' );

    % Check that the library loaded OK.
    ret = libisloaded ( 'htm_api' );
    
% ----- END ( vgsInit ) -----