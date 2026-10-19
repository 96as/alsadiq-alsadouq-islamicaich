import { createContext, useContext } from 'react';

export const NavVisibilityContext = createContext({
  hidden: false,
  setHidden: () => {},
});

export const useNavVisibility = () => useContext(NavVisibilityContext);
